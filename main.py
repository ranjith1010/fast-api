from fastapi import FastAPI, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
import pandas as pd
import ydata_profiling as pp
import csv
import codecs
import os


class FileDetail(BaseModel):
    path: str
    filename: str


base_directory = r'C:/Users/Public/data-profile/Repository'
if not os.path.exists(base_directory):
    os.mkdir(base_directory)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost.fr.world.socgen:3000",
    "http://localhost.fr.world.socgen:3000/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_folder_contents(folder_path):
    entries = []
    with os.scandir(folder_path) as items:
        for item in items:
            if item.is_file():
                if 'output' not in item.name:
                    entries.append({
                        "name": item.name.replace('.csv', ''),
                        "isFolder": False,
                    })
            elif item.is_dir():
                entries.append({
                    "name": item.name,
                    "isFolder": True,
                    "items": get_folder_contents(item.path)
                })
    return entries


def get_folders(folder_path, relative_path=""):
    entries = []
    with os.scandir(folder_path) as items:
        for item in items:
            if item.is_dir():
                prefix = relative_path + "/"
                if len(relative_path) == 0:
                    prefix = ""
                entries.append(prefix + item.name)
                sub_folders = get_folders(item.path, prefix + item.name)
                if len(sub_folders) > 0:
                    entries += sub_folders
    return entries


def parse_csv_up_to_json(file):
    csv_reader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
    data = []
    for rows in csv_reader:
        data.append(rows)

    return data


def parse_csv_to_json(filename):
    data = []
    with open(filename, encoding='utf-8') as csvf:
        csv_reader = csv.DictReader(csvf)
        for rows in csv_reader:
            data.append(rows)
    return data


def run_file(file_path):
    data = pd.read_csv(file_path, sep=',')
    filecount = len(data.index)
    data_types = pd.DataFrame(data.dtypes, columns=['Data Type'])
    completeness_data = pd.DataFrame(data.notnull().sum() / filecount * 100, columns=['Completeness %'])
    missing_data = pd.DataFrame(data.isnull().sum(), columns=['Missing Values'])
    uniqueness_values = pd.DataFrame(columns=['Uniqueness %']).astype(int)
    for row in list(data.columns.values):
        uniqueness_values.loc[row] = [data[row].nunique() / filecount * 100]
    sample_values = pd.DataFrame(columns=['Sample Value'])
    for row in list(data.columns.values):
        sample_values.loc[row] = [data[row].sample(5).unique().tolist()]
    max_length = pd.DataFrame(columns=['Maximum Length'])
    for row in list(data.columns.values):
        max_length.loc[row] = [data[row].astype(str).str.len().max()]
    min_length = pd.DataFrame(columns=['Minimum Length'])
    for row in list(data.columns.values):
        min_length.loc[row] = [data[row].astype(str).str.len().min()]
    format_values = pd.DataFrame(columns=['Format'])
    for row in list(data.columns.values):
        format_values.loc[row] = [
            data[row].astype(str).sample(10).replace('[0-9]', '9', regex=True).replace('[a-zA-Z]', 'X',
                                                                                       regex=True).replace('\W', 'S',
                                                                                                           regex=True).unique().tolist()]
    maximum_values = pd.DataFrame(columns=['Maximum Value'])
    for row in list(data.columns.values):
        maximum_values.loc[row] = [data[row].astype(str).max()]
    minimum_values = pd.DataFrame(columns=['Minimum Value'])
    for row in list(data.columns.values):
        minimum_values.loc[row] = [data[row].astype(str).min()]
    dq_report = data_types.join(completeness_data.astype(int)).join(uniqueness_values.astype(int)).join(
        max_length).join(min_length).join(maximum_values).join(minimum_values).join(format_values).join(sample_values)

    dq_report.to_csv(file_path.replace(".csv", "_output.csv"), sep=',')
    profile = pp.ProfileReport(data)
    profile.to_file(file_path.replace(".csv", "_output.html"))


@app.get("/folders")
async def get_folders_api():
    return get_folders(base_directory)


@app.get("/foldersAndFiles")
async def get_folders_files_api():
    return [{
        "name": 'Repository',
        "isFolder": True,
        "items": get_folder_contents(base_directory)
    }]


@app.post("/createAndSave")
async def create_folder_and_save_file_api(file: UploadFile,
                                          path: str = Form(...)):
    try:
        dir_path = base_directory + '/' + path
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            file_path = dir_path + '/profile_' + file.filename
            with open(file_path, "wb+") as file_object:
                file_object.write(file.file.read())
            run_file(file_path)
            return {"message": "Folder Created & File Saved Successfully"}
        else:
            file_path = dir_path + '/profile_' + file.filename
            if os.path.exists(file_path):
                os.remove(file_path)
                os.remove(file_path.replace('.csv', '_output.csv'))
                os.remove(file_path.replace('.csv', '_output.html'))
            with open(file_path, "wb+") as file_object:
                file_object.write(file.file.read())
            run_file(file_path)
            return {"message": "File Saved Successfully"}
    except:
        raise HTTPException(status_code=500, detail="Error while creating files/folder")


@app.post("/parseCsv")
async def parse_csv_to_json_api(file: UploadFile):
    return parse_csv_up_to_json(file)


@app.get("/inputData")
async def get_input_json_api(path: str):
    file = base_directory + '/' + path + '.csv'

    if os.path.exists(file):
        return parse_csv_to_json(file)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.delete("/deleteProfile")
async def delete_api(path: str):
    file = base_directory + '/' + path + '.csv'

    if os.path.exists(file):
        os.remove(file)
        os.remove(file.replace('.csv', '_output.csv'))
        os.remove(file.replace('.csv', '_output.html'))
        return {"message": "File Deleted Successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/profileData")
async def get_profile_json_api(path: str):
    file = base_directory + '/' + path + "_output.csv"
    if os.path.exists(file):
        return parse_csv_to_json(file)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/getReport")
async def get_report_api(path: str):
    file = base_directory + '/' + path + "_output.html"
    if os.path.exists(file):
        return FileResponse(file)
    else:
        raise HTTPException(status_code=404, detail="File not found")
