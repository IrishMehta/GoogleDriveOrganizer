import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from summarizing import Summarizer
from groq import Groq
import config

def authenticate():
    SCOPES = config.SCOPES

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_FILE, config.SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(config.TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

def list_files_in_folder(service, folder_id, master_list, folder_path=""):
    # Query to get files and folders in a specific folder
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, parents)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    items = results.get('files', [])

    for item in items:
        file_id = item['id']
        file_name = item['name']
        created_time = item.get('createdTime')
        modified_time = item.get('modifiedTime')
        mime_type = item.get('mimeType')

        # Check if the item is a folder or file
        if mime_type == 'application/vnd.google-apps.folder':
            # Recursively go through subfolders
            new_folder_path = f"{folder_path}/{file_name}"
            list_files_in_folder(service, file_id, master_list, new_folder_path)
        else:
            # File details
            file_path = f"{folder_path}/{file_name}"
            file_type = mime_type.split('/')[-1]  # Get the file type from mimeType
            master_list.append({
                'id': file_id,
                'name': file_name,
                'path': file_path,
                'mimeType': file_type,
                'createdTime': created_time,
                'modifiedTime': modified_time
            })
            print(f"File: {file_name}, Type: {file_type}, Path: {file_path}, Created: {created_time}, Modified: {modified_time}")
    return master_list




# LLM based classifier
def get_category_with_summary(category_string, summary):


    client = Groq(
        api_key=config.GROQ_API_KEY,
    )
    completion = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a File Categorizer"
            },
            {
                "role": "user",
                "content": "Given a text summary of a file that could be an image, pdf or a word document, categorize it into one of the following buckets" + str({', '.join(config.CATEGORIES)}) + "\nThe output should only be the name of the most relevant bucket\n\n" + str(summary)
            }
        ],
        temperature=0.1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )


    return completion.choices[0].message.content


def get_category(service, file_id, file_name, file_type):
    # Define keywords for each category
    summarizer = Summarizer(service)

    if file_type in ["pdf", "docx", "jpg", "jpeg", "png","msword"]:
        summary_text= summarizer.download_file(file_id, file_name, file_type)
        return get_category_with_summary(summary_text)
    else:
        # Define a fallback category for other file types
        # categories = json.loads(open(config.TAGGING_MAP_FILE).read())  # Using config for the tagging map

        # Group certain file types that aren't in the list into categories
        file_type_categories = {
            'csv': 'Data Files',
            'xlsx': 'Data Files',
            'txt': 'Text Files',
            'pptx': 'Presentations',
            'ppt': 'Presentations',
            'mp4': 'Videos',
            'avi': 'Videos',
            'mp3': 'Audio',
            'wav': 'Audio',
            'doc': 'Documents',
            'md': 'Documents',
        }

        # If the file type is recognized, assign a category based on the file type
        if file_type in file_type_categories:
            return file_type_categories[file_type]
        else:
            # # Otherwise, try to categorize based on keywords in the file name
            # for category, keywords in categories.items():
            #     if any(keyword.lower() in file_name.lower() for keyword in keywords):
            #         return category

            # Default to "Misc" if no category matches
            return "Misc"

## Updating a file
def create_folder_if_not_exists(service, name, parent_id=None):
    # Search for an existing folder with the same name
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and '{parent_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    items = results.get('files', [])

    if items:
        # Folder already exists, return its ID
        return items[0]['id']

    # Folder doesn't exist, create a new one
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')


def move_file(service, file_id, old_folder_id, new_folder_id):
    # Retrieve the existing parents to remove the file from old folders
    file = service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))

    # Move the file to the new folder
    service.files().update(
        fileId=file_id,
        addParents=new_folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()



def main():
    # Set your folder ID here

    # folder_id = '1NNo5q_AcQuQqv_rqWhcD0XhXoTpZRc4N'
    # Folder where data is present
    folder_id = config.FOLDER_ID

    # Folder where data is to be moved
    folder_move_id = config.FOLDER_MOVE_ID
    # Authentication
    creds = authenticate()

    # Initialize the service
    service = build("drive", "v3", credentials=creds)

    # Initialize the master list to store all files
    master_list = []

    # Start listing files from the root folder
    list_of_files = list_files_in_folder(service, folder_id, master_list)

    # Categorize and move files
    for i in list_of_files:
        category = get_category(service, i['id'], i['name'], i['mimeType'])
        new_folder_id = create_folder_if_not_exists(service, category, parent_id=folder_move_id)
        move_file(service, i['id'], folder_id, new_folder_id)


if __name__ == "__main__":
    main()