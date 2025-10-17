import re
import json
import os
import sys

def extract_components_blocks(file_content):
    chunkCB = extract_component_block_chunk_from_content(file_content)
    
    component_pattern = r'CID\s*=\s*(\S+).*?DBNAME1\s*=\s*"([^"]+)"'
    
    # Enhanced block pattern with better handling
    block_pattern = r'BLOCK\s+BLKID\s*=\s*(?:"([^"]+)"|(\w+))\s+BLKTYPE\s*=\s*(?:"([^"]+)"|(\w+)).*?IN\s*=\s*\(\s*([^)]+)\s*\).*?OUT\s*=\s*\(\s*([^)]+)\s*\)'
    
    matchesB = re.findall(block_pattern, chunkCB, re.DOTALL)
    matchesC = re.findall(component_pattern, chunkCB, re.DOTALL)
    
    # Process components
    components = []
    for match in matchesC:
        component_info = {
            'CID': match[0],
            'NAME': match[1]
        }
        components.append(component_info)
    
    # Process blocks with enhanced parsing
    blocks = []
    for match in matchesB:
        blkid = match[0] if match[0] else match[1]
        blktype = match[2] if match[2] else match[3]
        
        # Better stream parsing
        in_raw = match[4].strip()
        out_raw = match[5].strip()
        
        # Parse input streams more carefully
        in_streams = parse_stream_list(in_raw)
        out_streams = parse_stream_list(out_raw)
        
        block_info = {
            'BLKID': blkid,
            'BLKTYPE': blktype,
            'IN': in_streams,
            'OUT': out_streams
        }
        blocks.append(block_info)
    
    return components, blocks

def parse_stream_list(raw_streams):
    # Remove extra whitespace and split
    streams = []
    
    # Handle quoted and unquoted stream names
    # Split by whitespace but preserve quoted strings
    import shlex
    try:
        # Use shlex to properly handle quoted strings
        parsed = shlex.split(raw_streams)
        # Take every other item (skip the stream numbers/indices)
        streams = [parsed[i] for i in range(0, len(parsed), 2) if i < len(parsed)]
    except:
        # Fallback to simple splitting if shlex fails
        items = raw_streams.split()
        streams = [items[i] for i in range(0, len(items), 2) if i < len(items)]
    
    # Clean up stream names
    cleaned_streams = []
    for stream in streams:
        # Remove surrounding quotes if present
        stream = stream.strip().strip('"').strip("'")
        if stream:  # Only add non-empty streams
            cleaned_streams.append(stream)
    
    return cleaned_streams

def extract_component_block_chunk_from_content(content):
    lines = content.split('\n')
    found = False
    output = []
    
    for line in lines:
        if 'COMPONENTS' in line:
            found = True
        if found:
            if 'PROPERTIES' in line:
                found = False
                output.append(line)
                break
            output.append(line)
    
    return '\n'.join(output)

def format_blocks_for_bfd(blocks):
    formatted_blocks = []
    for block in blocks:
        # Format streams with quotes if they contain special characters
        in_streams_formatted = []
        for stream in block.get('IN', []):
            if '-' in stream or ' ' in stream:
                in_streams_formatted.append(f'"{stream}"')
            else:
                in_streams_formatted.append(stream)
        
        out_streams_formatted = []
        for stream in block.get('OUT', []):
            if '-' in stream or ' ' in stream:
                out_streams_formatted.append(f'"{stream}"')
            else:
                out_streams_formatted.append(stream)
        
        in_streams = ", ".join(in_streams_formatted)
        out_streams = ", ".join(out_streams_formatted)
        
        formatted_line = f"Block ID: {block.get('BLKID')} || Block Type: {block.get('BLKTYPE')} || IN: {in_streams} || OUT: {out_streams}"
        formatted_blocks.append(formatted_line)
    
    return '\n'.join(formatted_blocks)

def convert_blocks_to_json_format(blocks):
    """Convert blocks to the JSON format matching the example"""
    json_blocks = []
    
    for block in blocks:
        json_block = {
            "name": block.get('BLKID', ''),
            "type": block.get('BLKTYPE', ''),
            "input_streams": block.get('IN', []),
            "output_streams": block.get('OUT', [])
        }
        json_blocks.append(json_block)
    
    result = {
        "total_blocks": len(json_blocks),
        "blocks": json_blocks
    }
    
    return result

def save_to_json(data, output_filename='output.json', data_folder='data'):
    """Save data to JSON file in the specified data folder"""
    # Create data folder if it doesn't exist
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        print(f"Created folder: {data_folder}")
    
    # Full path to the output file
    output_path = os.path.join(data_folder, output_filename)
    
    # Write JSON file with proper formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"JSON file saved to: {output_path}")
    return output_path

def process_bkp_file_content(file_content, output_json=True, output_filename='output.json'):
    try:
        # Debug: Print the chunk being processed
        chunk = extract_component_block_chunk_from_content(file_content)
        print("DEBUG: Extracted chunk length:", len(chunk))
        
        components, blocks = extract_components_blocks(file_content)
        
        # Debug: Print number of blocks found
        print(f"DEBUG: Found {len(blocks)} blocks")
        for i, block in enumerate(blocks):
            print(f"Block {i+1}: {block['BLKID']} ({block['BLKTYPE']})")
        
        # Generate formatted text output
        formatted_result = format_blocks_for_bfd(blocks)
        
        # Generate and save JSON output if requested
        if output_json:
            json_data = convert_blocks_to_json_format(blocks)
            save_to_json(json_data, output_filename)
        
        return formatted_result
        
    except Exception as e:
        print(f"DEBUG: Error in processing: {str(e)}")
        raise Exception(f"Error processing BKP file: {str(e)}")

# Main execution
if __name__ == "__main__":
    # Check if filename was provided as argument
    if len(sys.argv) < 2:
        print("Usage: python bkp_parser.py <input_file.bkp> [output_file.json]")
        print("Example: python bkp_parser.py myfile.bkp")
        print("Example: python bkp_parser.py myfile.bkp custom_output.json")
        sys.exit(1)
    
    # Get input filename from command line argument
    input_file = sys.argv[1]
    
    # Get output filename from command line argument (optional)
    output_filename = sys.argv[2] if len(sys.argv) > 2 else 'blocks_output.json'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        sys.exit(1)
    
    print(f"Processing file: {input_file}")
    print(f"Output will be saved as: data/{output_filename}")
    print("-" * 50)
    
    # Read the BKP file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)
    
    # Process the file and save JSON output
    result = process_bkp_file_content(
        file_content, 
        output_json=True, 
        output_filename=output_filename
    )
    
    # Print the formatted text results
    print("\n" + "="*50)
    print("FORMATTED RESULTS:")
    print("="*50)
    print(result)