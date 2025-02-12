import os
import platform
import requests
import zipfile
import tarfile

opt_path = os.path.realpath(os.path.join(os.getcwd(), "opt"))
if not os.path.exists(opt_path):
    os.mkdir(opt_path)


def download_url(url: str, file_name: str = "file.zip", chunk_size: int = 512):
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    }
    req = requests.get(url, stream=True, allow_redirects=True, headers=headers)
    save_path = os.path.join(file_name)
    print(save_path)
    with open(save_path, "wb") as out_file:
        for chunk in req.iter_content(chunk_size=chunk_size):
            if chunk:
                out_file.write(chunk)


url_universalquantum = (
    "https://uqdevices.com/wp-content/uploads/2021/05/CD-V2.35.01.zip"
)
zip_universalquantum = os.path.join(opt_path, "CD-V2.35.01.zip")
if not os.path.exists(zip_universalquantum):
    download_url(url_universalquantum, zip_universalquantum)
    with zipfile.ZipFile(zip_universalquantum, "r") as zip:
        stub = "CD V2.35.01/Applications/DLL/Release_2_35/CTimeTag/"
        for file in zip.namelist():
            if file.startswith(stub):
                destination = zip.getinfo(file).filename.replace(stub[:-1], "CTimeTag")
                zip.getinfo(file).filename = destination
                zip.extract(file, path=os.path.relpath(opt_path))

if "Linux" in platform.platform():
    url_qutag = "https://qutools.com/files/quTAG/QUTAG-LX64QT5-V1.5.10.tgz"
    zip_qutag = os.path.join(opt_path, "QUTAG-LX64QT5-V1.5.10.tgz")
    if not os.path.exists(zip_qutag):
        download_url(url_qutag, zip_qutag)
    with tarfile.open(zip_qutag, "r") as tar:
        tar.extractall(opt_path)
    os.rename(
        os.path.join(opt_path, zip_qutag.replace(".tgz", "")),
        os.path.join(opt_path, "QUTAG"),
    )

# if "Windows" in platform.platform():
#     url_qutag = "https://qutools.com/files/quTAG/QUTAG-WIN64QT5-V1.5.10.zip"
#     zip_qutag = os.path.join(opt_path, "QUTAG-WIN64QT5-V1.5.10.zip")
#     if not os.path.exists(zip_qutag):
#         download_url(url_qutag, zip_qutag)
#     with zipfile.ZipFile(zip_qutag, 'r') as zip:
#         for file in zip.namelist():
#             if file.startswith("QUTAG-WIN64QT5-V1.5.10/"):
#                 zip.extract(file)
