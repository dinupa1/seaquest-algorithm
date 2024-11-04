import numpy as np
import matplotlib.pyplot as plt

import copy

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.data import random_split
from torch.utils.data import Dataset
from torch.optim.lr_scheduler import StepLR

import uproot
import awkward as ak

from sklearn.covariance import log_likelihood
from sklearn.metrics import roc_auc_score, roc_curve, auc
from sklearn.model_selection import train_test_split
from sklearn.utils import resample


class ResidualBlock(nn.Module):
    def __init__(self, input_featues: int=4, output_features: int = 32):
        super(ResidualBlock, self).__init__()

        self.conv_1 = nn.Sequential(
                nn.Conv2d(input_featues, output_features, kernel_size=3, padding=1),
                nn.BatchNorm2d(output_features),
            )
        self.relu_1 = nn.ReLU()
        self.conv_2 = nn.Sequential(
                nn.Conv2d(output_features, output_features, kernel_size=3, padding=1),
                nn.BatchNorm2d(output_features),
            )
        self.relu_2 = nn.ReLU()
        self.downsample = nn.Sequential(
                nn.Conv2d(input_featues, output_features, kernel_size=1, bias=False),
                nn.BatchNorm2d(output_features),
            )

    def forward(self, x):
        out = self.conv_1(x)
        out = self.relu_1(out)
        out = self.conv_2(out)
        identity = self.downsample(x)
        out += identity
        out = self.relu_2(out)
        return out


class ResNet(nn.Module):
    def __init__(self, input_featues: int=4, theta_features: int=12):
        super(ResNet, self).__init__()

        self.block_1 = ResidualBlock(input_featues, 16)
        self.maxpool_1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.block_2 = ResidualBlock(16, 32)
        self.maxpool_2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.block_3 = ResidualBlock(32, 64)
        self.avg_pool1 = nn.AvgPool2d(kernel_size=2, stride=2)
        self.fc_1 = nn.Sequential(
                nn.Linear(64* 1* 1 + theta_features, 64, bias=True),
                nn.BatchNorm1d(64),
                nn.ReLU(),
            )
        self.fc_2 = nn.Sequential(
                nn.Linear(64, 64, bias=True),
                nn.BatchNorm1d(64),
                nn.ReLU(),
            )
        self.fc_3 = nn.Sequential(
                nn.Linear(64, 1, bias=True),
                nn.Sigmoid(),
            )

    def forward(self, x, theta):
        x = self.block_1(x)
        x = self.maxpool_1(x)
        x = self.block_2(x)
        x = self.maxpool_2(x)
        x = self.block_3(x)
        x = self.avg_pool1(x)
        x = torch.flatten(x, 1)
        x = torch.cat([x, theta], dim=1)
        x = self.fc_1(x)
        x = self.fc_2(x)
        logit = self.fc_3(x)
        return logit
