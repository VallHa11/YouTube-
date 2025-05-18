from ninja import NinjaAPI, File, Form
from ninja.files import UploadedFile
from .models import Video,Comment,Reaction,Subscription
from .schemas import VideoOut,RegisterSchema,LoginSchema, CommentIn, CommentOut, SimpleVideo, UserProfileOut, ProfileUpdateIn, SimpleUser
from django.contrib.auth import get_user_model
from typing import Optional
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .auth import JWTAuth
from typing import List
from django.shortcuts import get_object_or_404
from django.db.models import Q




api = NinjaAPI(auth=JWTAuth())

User = get_user_model()

@api.post("/auth/register", auth=None)
def register(request, data: RegisterSchema):
    if User.objects.filter(username=data.username).exists():
        return {"error": "User already exists"}

    user = User.objects.create_user(
        username=data.username,
        password=data.password,
        email=data.email,
    )
    return {"message": "User created successfully"}


@api.post("/auth/login", auth=None)
def login(request, data: LoginSchema):
    user = authenticate(username=data.username, password=data.password)
    if not user:
        return {"error": "Invalid credentials"}

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

@api.post("/upload", response=VideoOut)
@api.post("/upload", response=VideoOut)
def upload_video(
    request,
    title: str = Form(...),
    description: str = Form(""),
    video_file: UploadedFile = File(...),
    thumbnail: Optional[UploadedFile] = File(None)
):
    user = request.user
    if not user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    video = Video.objects.create(
        title=title,
        description=description,
        video_file=video_file,
        thumbnail=thumbnail,
        author=user
    )

    return VideoOut(
        id=video.id,
        title=video.title,
        description=video.description,
        video_file=video.video_file.url,
        thumbnail=video.thumbnail.url if video.thumbnail else None,
        author_id=video.author.id,
        uploaded_at=video.uploaded_at,
        views=video.views,
        likes=0,
        dislikes=0,
    )


@api.post("/videos/{video_id}/comments/", response=CommentOut)
def create_comment(request, video_id: int, data: CommentIn):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    video = get_object_or_404(Video, id=video_id)
    comment = Comment.objects.create(
        video=video,
        author=request.user,
        text=data.text
    )
    return comment

@api.post("/videos/{video_id}/like")
def like_video(request, video_id: int):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    video = get_object_or_404(Video, id=video_id)
    reaction, created = Reaction.objects.update_or_create(
        user=request.user,
        video=video,
        defaults={"type": Reaction.LIKE}
    )
    return {"message": "Liked" if created else "Updated to like"}

@api.post("/videos/{video_id}/dislike")
def dislike_video(request, video_id: int):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    video = get_object_or_404(Video, id=video_id)
    reaction, created = Reaction.objects.update_or_create(
        user=request.user,
        video=video,
        defaults={"type": Reaction.DISLIKE}
    )
    return {"message": "Disliked" if created else "Updated to dislike"}

@api.get("/auth/me")
def me(request):
    if not request.user.is_authenticated:
        return {"error": "Not authenticated"}
    return {
        "id": request.user.id,
        "username": request.user.username,
        "email": request.user.email
    }

@api.get("/videos/", response=List[VideoOut])
def list_videos(request):
    videos = Video.objects.all().order_by("-uploaded_at")
    result = []
    for video in videos:
        result.append(VideoOut(
            id=video.id,
            title=video.title,
            description=video.description,
            video_file=video.video_file.url,
            thumbnail=video.thumbnail.url if video.thumbnail else None,
            author_id=video.author.id,
            uploaded_at=video.uploaded_at,
            views=video.views,
            likes=video.reactions.filter(type="like").count(),
            dislikes=video.reactions.filter(type="dislike").count()
        ))
    return result

@api.get("/videos/search", response=List[VideoOut])
def search_videos(request, q: str):
    videos = Video.objects.filter(
        Q(title__icontains=q) | Q(description__icontains=q)
    ).order_by("-uploaded_at")

    result = []
    for video in videos:
        result.append(VideoOut(
            id=video.id,
            title=video.title,
            description=video.description,
            video_file=video.video_file.url,
            thumbnail=video.thumbnail.url if video.thumbnail else None,
            author_id=video.author.id,
            uploaded_at=video.uploaded_at,
            views=video.views,
            likes=video.reactions.filter(type="like").count(),
            dislikes=video.reactions.filter(type="dislike").count()
        ))
    return result


@api.get("/videos/{video_id}", response=VideoOut)
def get_video(request, video_id: int):
    video = get_object_or_404(Video, id=video_id)
    video.likes = video.reactions.filter(type="like").count()
    video.dislikes = video.reactions.filter(type="dislike").count()
    video.views += 1
    video.save()
    return video

@api.get("/videos/{video_id}/comments/", response=List[CommentOut])
def list_comments(request, video_id: int):
    video = get_object_or_404(Video, id=video_id)
    return video.comments.all().order_by("-created_at")

@api.put("/comments/{comment_id}", response=CommentOut)
def update_comment(request, comment_id: int, data: CommentIn):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return api.create_response(request, {"error": "Permission denied"}, status=403)

    comment.text = data.text
    comment.save()
    return comment

@api.delete("/comments/{comment_id}")
def delete_comment(request, comment_id: int):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return api.create_response(request, {"error": "Permission denied"}, status=403)

    comment.delete()
    return {"message": "Comment deleted"}

@api.post("/subscribe/{user_id}")
def subscribe(request, user_id: int):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    to_user = get_object_or_404(User, id=user_id)

    if to_user == request.user:
        return api.create_response(request, {"error": "Cannot subscribe to yourself"}, status=400)

    sub, created = Subscription.objects.get_or_create(
        subscriber=request.user,
        subscribed_to=to_user
    )
    return {"message": "Subscribed" if created else "Already subscribed"}

@api.delete("/unsubscribe/{user_id}")
def unsubscribe(request, user_id: int):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    to_user = get_object_or_404(User, id=user_id)

    deleted, _ = Subscription.objects.filter(
        subscriber=request.user,
        subscribed_to=to_user
    ).delete()

    return {"message": "Unsubscribed" if deleted else "Was not subscribed"}

@api.get("/subscriptions/")
def list_subscriptions(request):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    subs = Subscription.objects.filter(subscriber=request.user).select_related("subscribed_to")
    return [{"id": sub.subscribed_to.id, "username": sub.subscribed_to.username} for sub in subs]

@api.get("/profile/", response=UserProfileOut)
def user_profile(request):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    user = request.user

    return UserProfileOut(
        id=user.id,
        username=user.username,
        email=user.email,
        subscribers_count=user.subscribers.count(),
        subscriptions_count=user.subscriptions.count(),
        videos=[
            SimpleVideo(
                id=v.id,
                title=v.title,
                uploaded_at=v.uploaded_at
            )
            for v in user.videos.all().order_by("-uploaded_at")
        ]
    )

@api.get("/users/{user_id}/", response=UserProfileOut)
def get_user_profile(request, user_id: int):
    user = get_object_or_404(User, id=user_id)
    return UserProfileOut(
        id=user.id,
        username=user.username,
        email=user.email,
        bio=user.bio,
        avatar=user.avatar.url if user.avatar else None,
        subscribers_count=user.subscribers.count(),
        subscriptions_count=user.subscriptions.count(),
        videos=[
            SimpleVideo(id=v.id, title=v.title, uploaded_at=v.uploaded_at)
            for v in user.videos.all().order_by("-uploaded_at")
        ]
    )

@api.put("/profile/", response=UserProfileOut)
def update_profile(request, data: ProfileUpdateIn):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    user = request.user
    if data.email:
        user.email = data.email
    if data.bio:
        user.bio = data.bio
    user.save()

    return get_user_profile(request, user.id)

@api.post("/profile/avatar/")
def upload_avatar(request, avatar: UploadedFile = File(...)):
    if not request.user.is_authenticated:
        return api.create_response(request, {"error": "Authentication required"}, status=401)

    user = request.user
    user.avatar.save(avatar.name, avatar)
    user.save()
    return {"message": "Avatar updated", "avatar": user.avatar.url}

@api.get("/users/search", response=List[SimpleUser])
def search_users(request, q: str):
    users = User.objects.filter(username__icontains=q).order_by("username")[:20]
    return [
        SimpleUser(
            id=u.id,
            username=u.username,
            avatar=u.avatar.url if u.avatar else None,
            bio=u.bio
        )
        for u in users
    ]

