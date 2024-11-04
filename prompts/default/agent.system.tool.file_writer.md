### file_writer:
Create or overwrite a file with specified content.
Use the following arguments:
- `filename`: The filename (no path) will be created or overwritten. 
- `content`: The content to write into the file.
- `folder`: The folder (relative) from the starting folder where you want the file to go. Use of '..' or '~' is forbidden.

**Example usage**:
~~~json
{
    "thoughts": [
        "The user has requested to create a file in a specified relative folder...",
        "I will use the file_writer tool to write the content to the specified file and folder."
    ],
    "tool_name": "file_writer",
    "tool_args": {
        "filename": "report.txt",  // The name of the file to create or overwrite
        "folder": "logs/reports",  // The relative folder where the file will be written
        "content": "Analysis complete. Summary included in this file."  // The content to be written into the file
    },
    "final_response": {
        "text": "The file report.txt has been successfully written to logs/reports."
    }
}

~~~%
