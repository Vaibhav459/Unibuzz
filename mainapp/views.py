from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from .models import Post, Comment, Tag, Conversation, Message, Notification, StudyGroup
from .moderation import contains_bad_words, is_image_inappropriate
import re
from .forms import UserUpdateForm, ProfileUpdateForm


def is_teacher_or_staff(user):
    return user.groups.filter(name__in=['Teacher', 'Staff']).exists()


def can_moderate(user):
    return user.is_superuser or is_teacher_or_staff(user)

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()


def login_page(request):
    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            student_group, created = Group.objects.get_or_create(name='Student')
            user.groups.add(student_group)

            messages.success(request, 'Account created successfully. You can now log in as a student.')
            return redirect('student_login')
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser or user.groups.filter(name='Student').exists():
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'You are not a student.')
        else:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'student_login.html')


def teacher_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        teacher_id = request.POST.get('teacher_id')

        user = authenticate(request, username=username, password=password)


        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('home')
            elif user.groups.filter(name__in=['Teacher', 'Staff']).exists():
                if user.profile.teacher_id == teacher_id:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid Teacher ID.')
            else:
                messages.error(request, 'You are not a teacher or staff user.')
        else:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'teacher_login.html')


@login_required
def user_logout(request):
    logout(request)
    return redirect('login_page')

@login_required
def home(request):
    tag_filter = request.GET.get('tag')
    if tag_filter:
        posts = Post.objects.filter(tags__name=tag_filter, group__isnull=True).order_by('-created_at')
    else:
        posts = Post.objects.filter(group__isnull=True).order_by('-created_at')
        
    moderator = can_moderate(request.user)

    followed_user_ids = request.user.following.all().values_list('user_id', flat=True)

    suggested_users = User.objects.exclude(
        id=request.user.id
    ).exclude(
        id__in=followed_user_ids
    )[:5]

    return render(request, 'home.html', {
        'posts': posts,
        'can_moderate': moderator,
        'is_admin': is_admin(request.user),
        'suggested_users': suggested_users,
        'current_tag': tag_filter,
    })


@login_required
def create_post(request):
    groups = StudyGroup.objects.all()
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        file_attachment = request.FILES.get('file_attachment')
        group_id = request.POST.get('group_id')

        is_question = request.POST.get('is_question') == 'on'

        group = None
        if group_id:
            group = StudyGroup.objects.get(id=group_id)

        if content or image or file_attachment:
            if contains_bad_words(content):
                profile = request.user.profile
                profile.warning_count += 1
                profile.save()
                messages.error(request, f'Your post contains inappropriate language. Warning {profile.warning_count}. Repeated violations may lead to a ban.')
                return redirect('create_post')

            if is_image_inappropriate(image, content):
                profile = request.user.profile
                profile.warning_count += 1
                profile.save()
                messages.error(request, f'Your post contains an inappropriate image. Warning {profile.warning_count}. Repeated violations may lead to a ban.')
                return redirect('create_post')

            post = Post.objects.create(
                user=request.user,
                content=content,
                image=image,
                file_attachment=file_attachment,
                is_question=is_question,
                group=group
            )
            
            if content:
                tags = re.findall(r'#(\w+)', content)
                for tag_name in tags:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    post.tags.add(tag)
                    
            messages.success(request, 'Post created successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Post must contain text, an image, or a file.')

    return render(request, 'create_post.html', {'groups': groups})


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
        if request.user != post.user:
            Notification.objects.create(recipient=post.user, sender=request.user, notification_type='like', post=post)

    return redirect('home')


@login_required
def toggle_bookmark(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    profile = request.user.profile
    if post in profile.saved_posts.all():
        profile.saved_posts.remove(post)
    else:
        profile.saved_posts.add(post)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            if contains_bad_words(content):
                profile = request.user.profile
                profile.warning_count += 1
                profile.save()
                messages.error(request, f'Your comment contains inappropriate language. Warning {profile.warning_count}. Repeated violations may lead to a ban.')
                return redirect(request.META.get('HTTP_REFERER', 'home'))

            Comment.objects.create(
                post=post,
                user=request.user,
                content=content
            )
            if request.user != post.user:
                Notification.objects.create(recipient=post.user, sender=request.user, notification_type='comment', post=post)

    return redirect('home')


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user == post.user or can_moderate(request.user):
        post.delete()
        messages.success(request, 'Post deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this post.')

    return redirect('home')


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user == comment.user or can_moderate(request.user):
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
    else:
        messages.error(request, 'You are not authorized to delete this comment.')

    return redirect('home')


@login_required
def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user_profile).order_by('-created_at')

    is_following = False
    if request.user.is_authenticated:
        is_following = request.user in user_profile.profile.followers.all()

    context = {
        'user_profile': user_profile,
        'posts': posts,
        'can_moderate': can_moderate(request.user),
        'is_following': is_following,
        'followers_count': user_profile.profile.followers.count(),
        'following_count': user_profile.following.count(),
    }

    return render(request, 'profile.html', context)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.user and not can_moderate(request.user):
        messages.error(request, 'You are not authorized to edit this post.')
        return redirect('home')

    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        remove_image = request.POST.get('remove_image')

        if content and contains_bad_words(content):
            profile = request.user.profile
            profile.warning_count += 1
            profile.save()
            messages.error(request, f'Your post contains inappropriate language. Warning {profile.warning_count}. Repeated violations may lead to a ban.')
            return redirect('edit_post', post_id=post.id)

        if image and is_image_inappropriate(image, content):
            profile = request.user.profile
            profile.warning_count += 1
            profile.save()
            messages.error(request, f'Your post contains an inappropriate image. Warning {profile.warning_count}. Repeated violations may lead to a ban.')
            return redirect('edit_post', post_id=post.id)

        post.content = content

        if remove_image == 'yes':
            post.image = None

        if image:
            post.image = image

        if post.content or post.image:
            post.save()
            messages.success(request, 'Post updated successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Post must contain text or an image.')

    return render(request, 'edit_post.html', {'post': post})


@login_required
def search(request):
    query = request.GET.get('query', '').strip()

    users = []
    posts = []

    if query:
        users = User.objects.filter(username__icontains=query)
        posts = Post.objects.filter(content__icontains=query).order_by('-created_at')

    return render(request, 'search.html', {
        'query': query,
        'users': users,
        'posts': posts
    })

@login_required
def moderation_panel(request):
    if not can_moderate(request.user):
        messages.error(request, 'You are not authorized to access the moderation panel.')
        return redirect('home')

    posts = Post.objects.all().order_by('-created_at')

    return render(request, 'moderation_panel.html', {
        'posts': posts
    })
@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile', username=request.user.username)
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'edit_profile.html', context)
@login_required
def follow_unfollow(request, username):
    target_user = get_object_or_404(User, username=username)
    target_profile = target_user.profile

    if request.user == target_user:
        messages.warning(request, "You cannot follow yourself.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    if request.user in target_profile.followers.all():
        target_profile.followers.remove(request.user)
        messages.success(request, f"You unfollowed {target_user.username}.")
    else:
        target_profile.followers.add(request.user)
        Notification.objects.create(recipient=target_user, sender=request.user, notification_type='follow')
        messages.success(request, f"You are now following {target_user.username}.")

    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def accept_answer(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post = comment.post
    
    if request.user == post.user:
        post.comments.update(is_accepted_answer=False)
        comment.is_accepted_answer = True
        comment.save()
        if request.user != comment.user:
            Notification.objects.create(recipient=comment.user, sender=request.user, notification_type='accept', post=post)
        messages.success(request, 'Answer accepted!')
    else:
        messages.error(request, 'Only the author can accept an answer.')
        
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def inbox(request):
    conversations = request.user.conversations.all().order_by('-updated_at')
    return render(request, 'inbox.html', {'conversations': conversations})

@login_required
def chat(request, username):
    other_user = get_object_or_404(User, username=username)
    
    if request.user == other_user:
        messages.warning(request, "You cannot message yourself.")
        return redirect('inbox')
        
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.save()
            Notification.objects.create(recipient=other_user, sender=request.user, notification_type='message')
            return redirect('chat', username=username)
            
    messages_list = conversation.messages.all().order_by('timestamp')
    messages_list.exclude(sender=request.user).update(is_read=True)
    
    return render(request, 'chat.html', {
        'conversation': conversation,
        'messages_list': messages_list,
        'other_user': other_user
    })

@login_required
def start_chat(request, username):
    return redirect('chat', username=username)

@login_required
def notifications(request):
    user_notifications = request.user.notifications.all().order_by('-created_at')
    user_notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': user_notifications})

@login_required
def groups_list(request):
    groups = StudyGroup.objects.all().order_by('-created_at')
    return render(request, 'groups_list.html', {'groups': groups})

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    posts = group.posts.all().order_by('-created_at')
    
    is_member = request.user in group.members.all()
    
    return render(request, 'group_detail.html', {
        'group': group,
        'posts': posts,
        'is_member': is_member,
        'can_moderate': can_moderate(request.user) or request.user == group.creator
    })

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name and description:
            group = StudyGroup.objects.create(
                name=name,
                description=description,
                creator=request.user
            )
            group.members.add(request.user)
            messages.success(request, 'Group created successfully!')
            return redirect('group_detail', group_id=group.id)
            
    return render(request, 'create_group.html')

@login_required
def join_leave_group(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    
    if request.user in group.members.all():
        group.members.remove(request.user)
        messages.success(request, f'You left {group.name}.')
    else:
        group.members.add(request.user)
        messages.success(request, f'You joined {group.name}!')
        
    return redirect('group_detail', group_id=group.id)

@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        messages.error(request, 'You are not authorized to access the admin dashboard.')
        return redirect('home')

    # We fetch all users except superusers
    users = User.objects.filter(is_superuser=False).order_by('-profile__warning_count')
    return render(request, 'admin_dashboard.html', {'users': users})

@login_required
def toggle_user_ban(request, user_id):
    if not is_admin(request.user):
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('home')
        
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user.is_superuser or is_admin(target_user):
        messages.error(request, 'You cannot ban a moderator or administrator.')
        return redirect('admin_dashboard')

    if target_user.is_active:
        target_user.is_active = False
        messages.success(request, f'User {target_user.username} has been banned.')
    else:
        target_user.is_active = True
        messages.success(request, f'User {target_user.username} has been unbanned.')
        
    target_user.save()
    return redirect('admin_dashboard')