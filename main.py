import os
import re
import requests
import argparse

ANYTHING_LLM_API_KEY = 'YOURAPIKEY'
ANYTHING_LLM_BASE_URL = 'http://AnythingLLM.local/api'
HEADERS = {'Authorization': f'Bearer {ANYTHING_LLM_API_KEY}'}


def list_workspaces():
    """List all workspaces with their names and correct file counts."""
    workspaces_url = f"{ANYTHING_LLM_BASE_URL}/v1/workspaces"
    documents_url = f"{ANYTHING_LLM_BASE_URL}/v1/documents"

    workspaces_resp = requests.get(workspaces_url, headers=HEADERS)
    workspaces = workspaces_resp.json().get('workspaces', [])
    workspace_info = {ws['id']: ws['name'] for ws in workspaces}
    workspace_file_counts = {ws['id']: 0 for ws in workspaces}

    documents_resp = requests.get(documents_url, headers=HEADERS)
    documents = documents_resp.json().get('localFiles', {}).get('items', [])

    def count_files(folder_items):
        total_unassigned = 0
        for item in folder_items:
            if item['type'] == 'file':
                ws_id = item.get('pinnedWorkspaces', [])
                if ws_id:
                    for id in ws_id:
                        if id in workspace_file_counts:
                            workspace_file_counts[id] += 1
                else:
                    total_unassigned += 1
            elif item['type'] == 'folder':
                total_unassigned += count_files(item['items'])
        return total_unassigned

    unassigned_count = count_files(documents)

    for ws_id, ws_name in workspace_info.items():
        print(f"Workspace: {ws_name}, Documents: {workspace_file_counts[ws_id]}")
    print(f"Unassigned Documents: {unassigned_count}")


def embed_files(regex_pattern, workspace_name):
    """Embeds files matching a regex pattern into the specified workspace by name."""
    workspace_slug = get_workspace_slug(workspace_name)
    if not workspace_slug:
        print(f"Error: Workspace '{workspace_name}' not found or slug could not be determined.")
        return

    print(f"Fetching document list to apply regex '{regex_pattern}'...")
    matched_files = get_matched_files(regex_pattern)

    if not matched_files:
        print(f"No files found matching pattern: {regex_pattern}")
        return

    print(f"Embedding {len(matched_files)} files matching pattern: '{regex_pattern}' into workspace: '{workspace_name}'")

    file_locations = [file['location'] for file in matched_files if 'location' in file]

    for location in file_locations:
        print(location)

    if file_locations:
        embed_result = embed_files_in_workspace(file_locations, workspace_slug)
        if embed_result:
            success_count = len(file_locations)
            print(f"Successfully embedded {success_count}/{len(matched_files)} files into workspace '{workspace_name}'.")
    else:
        print("No file locations found to embed.")


def get_workspace_slug(workspace_name):
    """Retrieve the slug for a given workspace name."""
    workspaces_url = f"{ANYTHING_LLM_BASE_URL}/v1/workspaces"
    response = requests.get(workspaces_url, headers=HEADERS)

    if response.status_code != 200:
        print("Failed to retrieve workspaces.")
        return None

    workspaces = response.json().get('workspaces', [])
    for ws in workspaces:
        if ws['name'].lower() == workspace_name.lower():
            return ws['slug']

    print(f"Workspace '{workspace_name}' not found.")
    return None


def embed_files_in_workspace(file_locations, workspace_slug):
    """Embeds a list of files into a specified workspace with debug output."""
    print(f"Attempting to embed files into workspace '{workspace_slug}' with the following locations: {file_locations}")

    embed_url = f"{ANYTHING_LLM_BASE_URL}/v1/workspace/{workspace_slug}/update-embeddings"
    data = {
        "adds": file_locations,
        "deletes": []
    }

    response = requests.post(embed_url, headers=HEADERS, json=data)

    if response.status_code == 200:
        print(f"Files successfully embedded into workspace '{workspace_slug}'")
        return True
    else:
        print(f"Failed to embed files into workspace '{workspace_slug}', Error: {response.status_code}")
        print(f"Response Content: {response.text}")
        return False

def get_matched_files(regex_pattern):
    """Helper function to retrieve and filter documents by regex pattern."""
    documents_url = f"{ANYTHING_LLM_BASE_URL}/v1/documents"
    print("Requesting list of all stored documents from AnythingLLM API...")
    documents_resp = requests.get(documents_url, headers=HEADERS)
    all_documents = documents_resp.json().get('localFiles', {}).get('items', [])

    matched_files = []

    def search_in_folder(folder_items, current_path=""):
        for item in folder_items:
            if item['type'] == 'file' and 'title' in item and re.search(regex_pattern, item['title']):
                # Erstelle den vollständigen Pfad basierend auf dem Ordnerpfad oder nutze Standardordner
                location = item.get('location', f"{current_path}/{item['name']}" if current_path else f"custom-documents/{item['name']}")
                matched_files.append({'title': item['title'], 'location': location})
            elif item['type'] == 'folder':
                # Rekursiv in Unterordner gehen, wobei der aktuelle Pfad erweitert wird
                search_in_folder(item['items'], f"{current_path}/{item['name']}" if current_path else item['name'])

    search_in_folder(all_documents)
    print(f"Total matched files: {len(matched_files)}")
    return matched_files


def upload_directory(directory_path):
    """Uploads all files in a specified directory to AnythingLLM."""
    if not os.path.isdir(directory_path):
        print(f"The path '{directory_path}' is not a valid directory.")
        return

    upload_url = f"{ANYTHING_LLM_BASE_URL}/v1/document/upload"
    success_count = 0
    total_files = 0

    for root, _, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            total_files += 1

            with open(file_path, 'rb') as file_data:
                files = {'file': (file_name, file_data)}
                response = requests.post(upload_url, headers=HEADERS, files=files)

                if response.status_code == 200:
                    print(f"Uploaded file: {file_name}")
                    success_count += 1
                else:
                    print(f"Failed to upload file: {file_name}, Status: {response.status_code}")
                    print(f"Response Content: {response.text}")

    print(f"Successfully uploaded {success_count}/{total_files} files from directory '{directory_path}'.")


def main():
    parser = argparse.ArgumentParser(description="AnythingLLM File Management CLI")
    parser.add_argument("-l", action="store_true", help="List all available workspaces and file counts")
    parser.add_argument("-u", type=str, help="Upload all files in a directory")
    parser.add_argument("-e", type=str, help="Embed files matching a regex pattern into a workspace")
    parser.add_argument("-w", type=str, help="Specify workspace name for embedding (required with -e)")

    args = parser.parse_args()

    if args.l:
        list_workspaces()
    elif args.u and args.e and args.w:
        upload_directory(args.u)
        embed_files(args.e, args.w)
    elif args.u:
        upload_directory(args.u)
    elif args.e:
        if not args.w:
            print("Error: Embedding requires a workspace name (-w) to be specified.")
            return
        embed_files(args.e, args.w)
    else:
        print("No valid command provided. Use --help for more information.")

if __name__ == "__main__":
    main()