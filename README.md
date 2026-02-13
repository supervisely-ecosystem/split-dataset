<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/115161827/209336313-db3b90d5-1b0b-488e-8900-1ed1f33b0b89.jpg"/>

# Split Datasets

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#split-methods">Split Methods</a> •
  <a href="#how-to-run">How To Run</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervisely.com/apps/supervisely-ecosystem/split-dataset)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/split-dataset)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/split-dataset)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/split-dataset)](https://supervisely.com)

</div>

# Overview

Application for splitting datasets in Supervisely projects. Supports flexible splitting of datasets with images, videos, point clouds, point cloud episodes, and volumetric data (DICOM/volumes) into parts using various methods. The application allows you to create new datasets in the current project, a new project, or an existing project, preserving all annotations and metadata. Ideal for preparing data for model training, creating validation subsets, or distributing data among project participants.

## Split Methods

### By Parts

The dataset is divided into equal parts of a specified number (from 1 to 1,000,000,000). Elements are distributed as evenly as possible, and if the number is not divisible evenly, the remaining elements are added one by one to the first parts.

### By Items Count

The dataset is divided into parts, each containing a **fixed number of elements**. The last part may contain fewer elements.

### By Percent

The dataset is divided into parts, each containing a specified **percentage of elements** from the original dataset.

**Important**: This method creates parts of equal size, not one part with the specified percentage! For example, specifying `10%` will create 10 parts, each containing 10% of the elements from the original dataset.

### By Ratio

The dataset is divided into parts according to a specified **numerical ratio**. This is the most flexible splitting method. The ratio in the format `number1:number2:number3:...` (e.g., `60:20:20` or `3:1:1`) defines the proportion of elements in each part. The numbers in the ratio do not necessarily have to sum to 100, as they are interpreted as proportions.

## Option: Random Order

When this option is activated, the dataset elements are **shuffled** randomly before splitting.

**How it works**:

1. All dataset elements are collected in a list
2. The list is randomly shuffled
3. The shuffled elements are distributed into parts according to the selected split method

## How to Run

### Step 1: Launch the application

Go to the list of projects in your Workspace and open the project context menu:

<img src="https://user-images.githubusercontent.com/115161827/209393639-1eb69ed0-e532-4288-96af-06b4473eacc7.gif">

### Step 2: Select dataset

Select one or more datasets to split.

### Step 3: Configure settings

1. **Select split method**: By Parts / By Items Count / By Percent / By Ratio
2. **Enter parameters** depending on the selected method
3. **(Optional)** Enable "Random Order" to shuffle elements
4. **Select save location**: current project / new project / existing project

### Step 4: Run

Click the `Start` button and wait for the process to complete.

## Screenshot

<img src="https://user-images.githubusercontent.com/115161827/209395515-813138fd-0d0f-40b4-92d1-10d39b7e149a.png">
