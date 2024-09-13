import supervisely as sly
from supervisely.app.widgets import Button, Card, Table, Text, Container, Flexbox
import src.globals as g
import pandas as pd


COL_ID = "dataset id".upper()
COL_NAME = "dataset name".upper()
COL_DESCRIPTION = "dataset description".upper()
COL_COUNT = "elements in dataset".upper()
SELECT_DATASET = "select".upper()

selected_datasets_names = set()
selected_datasets = Text(f"Selected dataset: ")

columns = [
    COL_ID,
    COL_NAME,
    COL_DESCRIPTION,
    COL_COUNT,
    SELECT_DATASET,
]

table = Table(fixed_cols=2, width="100%")


def build_table():
    global table
    rows = []
    table.loading = True

    datasets = g.api.dataset.get_list(g.PROJECT_ID)
    g.DATASETS_INFO = {dataset.id: dataset for dataset in datasets}
    for dataset in datasets:
        rows.append(
            [
                dataset.id,
                dataset.name,
                dataset.description,
                dataset.items_count,
                "",
            ]
        )
    df = pd.DataFrame(rows, columns=columns)
    table.read_pandas(df)
    table.loading = False


@table.click
def handle_table_button(datapoint: sly.app.widgets.Table.ClickedDataPoint):
    row = datapoint.row
    dataset_id = row[COL_ID]
    dataset_name = row[COL_NAME]
    if row[SELECT_DATASET] == "✅":
        if dataset_id in g.SELECTED_DATASETS_IDS:
            g.SELECTED_DATASETS_IDS.remove(dataset_id)
        if dataset_name in selected_datasets_names:
            selected_datasets_names.remove(dataset_name)
        table.update_cell_value(COL_ID, dataset_id, SELECT_DATASET, "")
    else:
        g.SELECTED_DATASETS_IDS.add(dataset_id)
        selected_datasets_names.add(dataset_name)
        table.update_cell_value(COL_ID, dataset_id, SELECT_DATASET, "✅")
    table.clear_selection()
    selected_datasets.set(f'Selected datasets: {", ".join(list(selected_datasets_names))}', "text")


select_all_button = Button("Select all", button_type="text", icon="zmdi zmdi-check-all")
deselect_all_button = Button("Deselect all", button_type="text", icon="zmdi zmdi-square-o")
update_table_button = Button("Refresh", button_type="text", icon="zmdi zmdi-refresh")


@select_all_button.click
def select_all_datasets():
    global selected_datasets_names
    g.SELECTED_DATASETS_IDS = set([id for id in g.DATASETS_INFO.keys()])
    selected_datasets_names = set([dataset.name for dataset in g.DATASETS_INFO.values()])
    selected_datasets.set(f'Selected datasets: {", ".join(list(selected_datasets_names))}', "text")
    table.update_matching_cells(SELECT_DATASET, "", SELECT_DATASET, "✅")


@deselect_all_button.click
def deselect_all_datasets():
    global selected_datasets_names
    g.SELECTED_DATASETS_IDS = set()
    selected_datasets_names = set()
    selected_datasets.set(f'Selected datasets: {", ".join(list(selected_datasets_names))}', "text")
    table.update_matching_cells(SELECT_DATASET, "✅", SELECT_DATASET, "")


@update_table_button.click
def update_table():
    global selected_datasets_names
    g.SELECTED_DATASETS_IDS = set()
    selected_datasets_names = set()
    selected_datasets.set(f'Selected datasets: {", ".join(list(selected_datasets_names))}', "text")
    build_table()


dataset_selector_card = Card(
    "2️⃣ Select dataset",
    "Choose the datasets to split. Click on a row to select",
    collapsable=False,
    content=Container(
        widgets=[
            Flexbox(widgets=[update_table_button, select_all_button, deselect_all_button]),
            table,
        ]
    ),
)
