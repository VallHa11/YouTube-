from ninja import Router, File, Form
from ninja.files import UploadedFile
from ninja.params import Body
from django.conf import settings
from .models import VideoUpload, Video
import os

router = Router()

@router.post("/upload-chunk/")
def upload_chunk(
    request,
    upload_id: str = Form(...),
    chunk_number: int = Form(...),
    total_chunks: int = Form(...),
    file_name: str = Form(...),
    file: UploadedFile = File(...)
):
    # тут уже нет data["upload_id"] — просто используешь переменные напрямую
    video_upload, created = VideoUpload.objects.get_or_create(
        upload_id=upload_id,
        defaults={'file_name': file_name, 'total_chunks': total_chunks}
    )

    chunk_dir = os.path.join(settings.CHUNK_UPLOAD_DIR, upload_id)
    os.makedirs(chunk_dir, exist_ok=True)

    chunk_path = os.path.join(chunk_dir, f"{chunk_number}.part")
    with open(chunk_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    video_upload.uploaded_chunks += 1
    video_upload.save()

    if video_upload.uploaded_chunks >= video_upload.total_chunks:
        video_upload.is_complete = True
        video_upload.save()
        full_video_path = assemble_chunks(upload_id, file_name)
        create_video_record(request.user, full_video_path, file_name)

    return {"message": f"Chunk {chunk_number} uploaded"}

def assemble_chunks(upload_id, file_name):
    chunk_dir = os.path.join(settings.CHUNK_UPLOAD_DIR, upload_id)
    full_video_path = os.path.join(settings.VIDEO_STORAGE_DIR, file_name)

    with open(full_video_path, 'wb') as outfile:
        for i in range(1, len(os.listdir(chunk_dir)) + 1):
            part_path = os.path.join(chunk_dir, f"{i}.part")
            with open(part_path, 'rb') as infile:
                outfile.write(infile.read())

    for f in os.listdir(chunk_dir):
        os.remove(os.path.join(chunk_dir, f))
    os.rmdir(chunk_dir)

    convert_to_hls(full_video_path)
    return full_video_path

def convert_to_hls(input_path):
    output_dir = input_path.replace('.mp4', '')
    os.makedirs(output_dir, exist_ok=True)
    command = f'ffmpeg -i "{input_path}" -profile:v baseline -level 3.0 -start_number 0 -hls_time 10 -hls_list_size 0 -f hls "{output_dir}/index.m3u8"'
    os.system(command)

def create_video_record(user, full_video_path, file_name):
    Video.objects.create(
        title=file_name,
        description="Uploaded via chunk upload",
        video_file=f"videos/{file_name}",
        author=user
    )
