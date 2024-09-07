from django.urls import path, include
from .views import upload_data, home, search_view, user, profile, chat, procedure, favorite, plan, medical_record, cid

urlpatterns = [
    path('upload_files/', upload_data.UploadDataView.as_view(), name='upload_files'),
    path('', home.Home.as_view(), name='home'),
    path('search/', search_view.SearchView.as_view(), name='search'),
    path('login/', user.LoginView.as_view(), name='login'),
    path('logout/', user.LogoutView.as_view(), name='logout'),
    path('profile/', profile.ProfileView.as_view(), name='profile'),
    path('register/<selected_plan>/', user.RegisterView.as_view(), name='register'),
    path('chat/', chat.ChatView.as_view(), name='chat'),
    path('procedure/<str:procedure_code>/', procedure.DetailView.as_view(), name='procedure_detail'),
    path('procedures/', procedure.ListView.as_view(), name='procedure_list'),
    path('more_procedures/', procedure.LoadMoreView.as_view(), name='procedure_more'),
    path('procedures/favorite', favorite.FavoriteView.as_view(), name='procedure_favorite'),
    path('check_favorite/', favorite.CheckFavoriteView.as_view(), name='check_favorite'),
    path('add-remove-favorite/', favorite.ToggleFavoriteView.as_view(), name='add_remove_favorite'),
    path('favorite_folder_edit/<int:folder_id>/', favorite.EditFolderView.as_view(), name='favorite_folder_edit'),
    path('favorite_folder_delete/<int:folder_id>/', favorite.DeleteFolderView.as_view(), name='favorite_folder_delete'),
    path('search_favorites/', favorite.FavoriteProceduresListView.as_view(), name='search_favorites'),
    path('add_new_favorite_folder/', favorite.CreateFolderView.as_view(), name='add_new_favorite_folder'),
    path('select_plan/', plan.PlanView.as_view(), name='select_plan'),
    path('medical_record/', medical_record.MedicalRecordView.as_view(), name='medical_record'),
    path('procedure-autocomplete/', procedure.ProcedureAutocomplete.as_view(), name='procedure-autocomplete'),
    path('cid-autocomplete/', cid.CidAutocomplete.as_view(), name='cid-autocomplete'),
    path('password_reset/', user.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/<uidb64>/<token>/', user.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('activate/<uidb64>/<token>', user.activate, name='verify_email'),
    path('cid_autocomplete/', medical_record.CidAutocompleteView.as_view(), name='cid-autocomplete'),
    path('api/', include('cbo.api.urls'), name='cbo_api')
]
