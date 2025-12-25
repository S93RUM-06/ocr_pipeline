using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using RoiSampler.Core.Models;
using RoiSampler.Core.Services;
using System.Collections.ObjectModel;
using System.Linq;

namespace RoiSampler.App.ViewModels;

public partial class ProfileManagerViewModel : ObservableObject
{
    private readonly ProfileManager _profileManager;

    [ObservableProperty]
    private ObservableCollection<FieldSetProfile> _profiles = new();

    [ObservableProperty]
    private FieldSetProfile? _selectedProfile;

    [ObservableProperty]
    private string _statusMessage = string.Empty;

    [ObservableProperty]
    private bool _isEditing;

    public ProfileManagerViewModel()
    {
        _profileManager = new ProfileManager();
        LoadProfiles();
    }

    /// <summary>
    /// 載入所有 Profiles
    /// </summary>
    [RelayCommand]
    private void LoadProfiles()
    {
        Profiles.Clear();
        var profiles = _profileManager.ListProfiles();

        foreach (var profile in profiles)
        {
            Profiles.Add(profile);
        }

        StatusMessage = $"已載入 {Profiles.Count} 個 Profile";

        // 如果有 Profile，自動選擇第一個
        if (Profiles.Count > 0 && SelectedProfile == null)
        {
            SelectedProfile = Profiles[0];
        }
    }

    /// <summary>
    /// Profile 選擇變更 - 觸發 UI 更新
    /// </summary>
    partial void OnSelectedProfileChanged(FieldSetProfile? value)
    {
        // 觸發屬性變更通知，讓 DataGrid 知道要重新綁定
        OnPropertyChanged(nameof(SelectedProfile));

        if (value != null)
        {
            StatusMessage = $"已選擇: {value.ProfileName} ({value.Fields.Count} 個欄位)";
        }
        else
        {
            StatusMessage = "未選擇 Profile";
        }

        // 確保不在編輯模式
        IsEditing = false;
    }

    /// <summary>
    /// 建立新 Profile
    /// </summary>
    [RelayCommand]
    private void CreateNewProfile()
    {
        var profileName = $"新 Profile {Profiles.Count + 1}";
        var newProfile = _profileManager.CreateNewProfile(profileName);

        // 加入預設欄位
        newProfile.Fields.Add(new FieldDefinition
        {
            FieldName = "field_1",
            DisplayName = "欄位 1",
            DataType = "string",
            Required = false
        });

        Profiles.Add(newProfile);
        SelectedProfile = newProfile;
        IsEditing = true;

        StatusMessage = $"已建立新 Profile: {profileName}";
    }

    /// <summary>
    /// 複製 Profile
    /// </summary>
    [RelayCommand]
    private void CloneProfile()
    {
        if (SelectedProfile == null)
        {
            StatusMessage = "請先選擇要複製的 Profile";
            return;
        }

        var newName = $"{SelectedProfile.ProfileName} (副本)";
        var cloned = _profileManager.CloneProfile(SelectedProfile, newName);

        Profiles.Add(cloned);
        SelectedProfile = cloned;
        IsEditing = true;

        StatusMessage = $"已複製 Profile: {newName}";
    }

    /// <summary>
    /// 儲存 Profile
    /// </summary>
    [RelayCommand]
    private void SaveProfile()
    {
        if (SelectedProfile == null)
        {
            StatusMessage = "沒有選擇的 Profile";
            return;
        }

        var errors = _profileManager.ValidateProfile(SelectedProfile);
        if (errors.Count > 0)
        {
            StatusMessage = $"驗證失敗: {string.Join(", ", errors)}";
            return;
        }

        try
        {
            _profileManager.SaveProfile(SelectedProfile);
            IsEditing = false;
            StatusMessage = $"✅ 已儲存: {SelectedProfile.ProfileName}";
        }
        catch (System.Exception ex)
        {
            StatusMessage = $"❌ 儲存失敗: {ex.Message}";
        }
    }

    /// <summary>
    /// 刪除 Profile
    /// </summary>
    [RelayCommand]
    private void DeleteProfile()
    {
        if (SelectedProfile == null)
        {
            StatusMessage = "請先選擇要刪除的 Profile";
            return;
        }

        var profileName = SelectedProfile.ProfileName;
        var profileToDelete = SelectedProfile;

        // 先取消選擇
        SelectedProfile = null;

        // 從列表中移除
        Profiles.Remove(profileToDelete);

        // 刪除檔案
        _profileManager.DeleteProfile(profileToDelete.ProfileId);

        StatusMessage = $"已刪除: {profileName}";
    }

    /// <summary>
    /// 新增欄位
    /// </summary>
    [RelayCommand]
    private void AddField()
    {
        if (SelectedProfile == null)
        {
            StatusMessage = "請先選擇或建立 Profile";
            return;
        }

        var fieldName = $"field_{SelectedProfile.Fields.Count + 1}";
        var newField = new FieldDefinition
        {
            FieldName = fieldName,
            DisplayName = $"欄位 {SelectedProfile.Fields.Count + 1}",
            DataType = "string",
            Required = false
        };

        SelectedProfile.Fields.Add(newField);

        // 強制觸發 UI 更新
        OnPropertyChanged(nameof(SelectedProfile));

        StatusMessage = $"已新增欄位: {fieldName}";
    }

    /// <summary>
    /// 刪除欄位
    /// </summary>
    [RelayCommand]
    private void DeleteField(FieldDefinition field)
    {
        if (SelectedProfile == null || field == null) return;

        SelectedProfile.Fields.Remove(field);

        // 強制觸發 UI 更新
        OnPropertyChanged(nameof(SelectedProfile));

        StatusMessage = $"已刪除欄位: {field.FieldName}";
    }

    /// <summary>
    /// 開始編輯
    /// </summary>
    [RelayCommand]
    private void StartEdit()
    {
        if (SelectedProfile == null)
        {
            StatusMessage = "請先選擇 Profile";
            return;
        }

        IsEditing = true;
        StatusMessage = $"編輯模式: {SelectedProfile.ProfileName}";
    }

    /// <summary>
    /// 取消編輯
    /// </summary>
    [RelayCommand]
    private void CancelEdit()
    {
        IsEditing = false;

        // 重新載入以還原變更
        var currentProfileId = SelectedProfile?.ProfileId;
        LoadProfiles();

        // 恢復選擇
        if (currentProfileId != null)
        {
            SelectedProfile = Profiles.FirstOrDefault(p => p.ProfileId == currentProfileId);
        }

        StatusMessage = "已取消編輯";
    }
}