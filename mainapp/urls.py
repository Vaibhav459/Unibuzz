from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.login_page, name='login_page'),

    path('home/', views.home, name='home'),

    path('register/', views.register, name='register'),
    path('follow/<str:username>/', views.follow_unfollow, name='follow_unfollow'),


    path('login/', views.student_login, name='login'),
    path('student/login/', views.student_login, name='student_login'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),

    path('logout/', views.user_logout, name='user_logout'),

    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    path('create/', views.create_post, name='create_post'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),

    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('bookmark/<int:post_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),

    path('search/', views.search, name='search'),
    path('moderation/', views.moderation_panel, name='moderation_panel'),

    path('accept-answer/<int:comment_id>/', views.accept_answer, name='accept_answer'),
    path('inbox/', views.inbox, name='inbox'),
    path('chat/<str:username>/', views.chat, name='chat'),
    path('start-chat/<str:username>/', views.start_chat, name='start_chat'),
    path('notifications/', views.notifications, name='notifications'),
    path('groups/', views.groups_list, name='groups_list'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/join/', views.join_leave_group, name='join_leave_group'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('ban-user/<int:user_id>/', views.toggle_user_ban, name='toggle_user_ban'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)