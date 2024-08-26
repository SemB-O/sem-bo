from django.urls import path, include
from .views import UploadFilesView, Home, SearchView, UserLoginView, LogoutView, ChatView, ProcedureDetailView, ProcedureListView, ProcedureLoadMoreView, UserRegistrationView, UserProfileView, ProcedureFavoriteView, AddRemoveFavoriteView, FavoriteProcedureListView, activate, PasswordResetRequestView, PasswordResetConfirmView, SelectPlanView, CreateFavoriteFolderView, CheckFavoriteView, EditFolderView, DeleteFolderView, MedicalRecordHomeView, ProcedureAutocomplete, CidAutocomplete

urlpatterns = [
    path('upload_files/', UploadFilesView.as_view(), name='upload_files'),
    path('', Home.as_view(), name='home'),
    path('search/', SearchView.as_view(), name='search'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('register/<selected_plan>/', UserRegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('procedure/<str:procedure_code>/', ProcedureDetailView.as_view(), name='procedure_detail'),
    path('procedures/', ProcedureListView.as_view(), name='procedure_list'),
    path('procedures/favorite', ProcedureFavoriteView.as_view(), name='procedure_favorite'),
    path('check_favorite/', CheckFavoriteView.as_view(), name='check_favorite'),
    path('add-remove-favorite/', AddRemoveFavoriteView.as_view(), name='add_remove_favorite'),
    path('favorite_folder_edit/<int:folder_id>/', EditFolderView.as_view(), name='favorite_folder_edit'),
    path('favorite_folder_delete/<int:folder_id>/', DeleteFolderView.as_view(), name='favorite_folder_delete'),
    path('more_procedures/', ProcedureLoadMoreView.as_view(), name='procedure_more'),
    path('search_favorites/', FavoriteProcedureListView.as_view(), name='search_favorites'),
    path('add_new_favorite_folder/', CreateFavoriteFolderView.as_view(), name='add_new_favorite_folder'),
    path('select_plan/', SelectPlanView.as_view(), name='select_plan'),
    path('medical_record/', MedicalRecordHomeView.as_view(), name='medical_record'),
    path('procedure-autocomplete/', ProcedureAutocomplete.as_view(), name='procedure-autocomplete'),
    path('cid-autocomplete/', CidAutocomplete.as_view(), name='cid-autocomplete'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password_reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('activate/<uidb64>/<token>', activate, name='verify_email'),
    path('api/', include('cbo.api.urls'), name='cbo_api')
]
