import sys
import json
import re
import os
import argparse

# Updated regex pattern to match more specific figure references
image_pattern = re.compile(r"^(Fig\.|Figure)\s(\d+(\.\d+)?(\s*\([a-z]\))?)")
table_pattern = re.compile(r"^(Table)\s(\d+(\.\d+)?(\s*\([a-z]\))?)")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process files from an input directory and save them to an output directory.')
    
    # Add the output directory argument
    parser.add_argument('-o', '--output', type=str, required=True,
                        help='Output directory path')
    
    # Add the input directory argument
    parser.add_argument('input_dir', type=str, 
                        help='Input directory path')

    # Parse the command-line arguments
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output

    # Ensure the output directory exists, if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    # Process each file with the specified suffix in the input directory
    content_list_file = None
    suffix = "_content_list.json"
    for filename in os.listdir(input_dir):
        if filename.endswith(suffix):
           content_list_file = os.path.join(input_dir, filename)
           break
           
    if content_list_file is None:
        print(f"Error: No file with suffix '{suffix}' found in the input directory.")
        return
    
    try:
      with open (content_list_file, 'r') as f:
        data = f.read()
        data = json.loads(data)
      
      # Initialize lists to hold tables and images
      tables = []
      images = []

      # Iterate over the JSON data
      for item in data:
        if item.get("type") == "table":
            tables.append(item)
        elif item.get("type") == "image":
            images.append(item)

      for image in images:
          for caption in image.get("img_caption"):
              description = []
              match = image_pattern.match(caption)
              if match:
                matched_part = match.group(0)  # Get the entire matched string
                image['ref'] = matched_part
                description.append(caption.replace(matched_part, '').strip())
              else:
                description.append(caption)
              image['description'] = ';'.join(description)


      for table in tables:
          for caption in table.get("table_caption"):
              match = table_pattern.match(caption)
              description = []
              if match:
                matched_part = match.group(0)  # Get the entire matched string
                table['ref'] = matched_part
                description.append(caption.replace(matched_part, '').strip())
              else:
                description.append(caption)
              table['description'] = ';'.join(description)

      with open(os.path.join(output_dir, 'image-table-list.json'), 'w') as f:
        json.dump(images+tables, f, indent=2)

      # in the markdown file, search for the image/table reference and insert the file name like: ![Figure 1](images/figure1.png)
      suffix = ".md"
      for filename in os.listdir(input_dir):
        if filename.endswith(suffix):
          markdown_file = os.path.join(input_dir, filename)

          with open(markdown_file, 'r') as f:
              content = f.read()

          # remove all file names like ![](images/figure1.png)
          content = re.sub(r'!\[\]\(images/.*?\)', '', content)

          for item in images+tables:
            if item.get('ref'):
              desc = f"{item.get('ref')} {item.get('description')}".strip()
              content = content.replace(item.get('ref'), f"![{desc}]({item.get('img_path')})")

          output_file = os.path.join(output_dir, filename)

          with open(output_file, 'w') as f:
            f.write(content)

    except FileNotFoundError:
        print(f"Error: The file does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
