import os

def convert_to_hls(input_path):
    output_dir = input_path.replace('.mp4', '')
    os.makedirs(output_dir, exist_ok=True)
    command = f'ffmpeg -i "{input_path}" -profile:v baseline -level 3.0 -start_number 0 -hls_time 10 -hls_list_size 0 -f hls "{output_dir}/index.m3u8"'
    os.system(command)
