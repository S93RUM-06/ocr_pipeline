using Avalonia.Media.Imaging;
using Avalonia.Platform.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using RoiSampler.Core.Models;
using RoiSampler.Core.Services;
using RoiSampler.Core.Statistics;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace RoiSampler.App.ViewModels;

public partial class MainWindowViewModel : ViewModelBase
{
    private readonly ProfileManager _profileManager;
    private readonly TemplateCalculator _templateCalculator;
    private int _nextSampleId = 1;

    [ObservableProperty]
    private Bitmap? _currentImage;

    [ObservableProperty]
    private double _imageWidth;

    [ObservableProperty]
    private double _imageHeight;

    [ObservableProperty]
    private string _statusMessage = "準備就緒";

    [ObservableProperty]
    private ObservableCollection<ImageSample> _samples = new();

    [ObservableProperty]
    private ImageSample? _selectedSample;

    [ObservableProperty]
    private ObservableCollection<RoiAnnotation> _annotations = new();

    [ObservableProperty]
    private string? _currentFieldName;

    [ObservableProperty]
    private bool _isDrawing;

    [ObservableProperty]
    private double _startX;

    [ObservableProperty]
    private double _startY;

    [ObservableProperty]
    private double _currentX;

    [ObservableProperty]
    private double _currentY;

    // Profile 相關屬性
    [ObservableProperty]
    private ObservableCollection<FieldSetProfile> _availableProfiles = new();

    [ObservableProperty]
    private FieldSetProfile? _selectedProfile;

    [ObservableProperty]
    private ObservableCollection<FieldDefinition> _currentFields = new();

    // 範本計算結果
    [ObservableProperty]
    private TemplateSchema? _calculatedTemplate;

    [ObservableProperty]
    private List<string> _qualityWarnings = new();

    public MainWindowViewModel()
    {
        _profileManager = new ProfileManager();
        _templateCalculator = new TemplateCalculator();
        LoadProfiles();
    }

    /// <summary>
    /// 載入所有可用的 Profiles
    /// </summary>
    [RelayCommand]
    private void LoadProfiles()
    {
        AvailableProfiles.Clear();
        var profiles = _profileManager.ListProfiles();
        
        foreach (var profile in profiles)
        {
            AvailableProfiles.Add(profile);
        }

        StatusMessage = $"已載入 {AvailableProfiles.Count} 個 Profile";
    }

    /// <summary>
    /// Profile 選擇變更 - 載入欄位列表
    /// </summary>
    partial void OnSelectedProfileChanged(FieldSetProfile? value)
    {
        CurrentFields.Clear();
        
        if (value != null)
        {
            foreach (var field in value.Fields)
            {
                CurrentFields.Add(field);
            }
            StatusMessage = $"已載入 Profile: {value.ProfileName} ({value.Fields.Count} 個欄位)";
        }
    }

    /// <summary>
    /// 從 Profile 載入欄位到當前工作區
    /// </summary>
    [RelayCommand]
    private void ApplyProfile()
    {
        if (SelectedProfile == null)
        {
            StatusMessage = "請先選擇 Profile";
            return;
        }

        CurrentFields.Clear();
        foreach (var field in SelectedProfile.Fields)
        {
            CurrentFields.Add(field);
        }

        StatusMessage = $"已套用 Profile: {SelectedProfile.ProfileName}，請依序標註 {CurrentFields.Count} 個欄位";
    }

    /// <summary>
    /// 開啟 Profile 管理視窗
    /// </summary>
    [RelayCommand]
    private async Task OpenProfileManager()
    {
        var window = new Views.ProfileManagerWindow();
        await window.ShowDialog(App.Current?.ApplicationLifetime is Avalonia.Controls.ApplicationLifetimes.IClassicDesktopStyleApplicationLifetime desktop 
            ? desktop.MainWindow 
            : null);
        
        // 對話框關閉後重新載入 Profiles
        LoadProfiles();
    }

    /// <summary>
    /// 載入單張圖片（內部使用）
    /// </summary>
    private async Task LoadImageInternalAsync(string filePath)
    {
        try
        {
            if (!File.Exists(filePath))
            {
                StatusMessage = $"找不到檔案: {filePath}";
                return;
            }

            using var stream = File.OpenRead(filePath);
            CurrentImage = await Task.Run(() => Bitmap.DecodeToWidth(stream, 1200));
            
            ImageWidth = CurrentImage.Size.Width;
            ImageHeight = CurrentImage.Size.Height;

            StatusMessage = $"已載入: {Path.GetFileName(filePath)} ({ImageWidth}x{ImageHeight})";
        }
        catch (Exception ex)
        {
            StatusMessage = $"載入失敗: {ex.Message}";
        }
    }

    /// <summary>
    /// 載入單張圖片並建立樣本
    /// </summary>
    [RelayCommand]
    private async Task LoadSingleImageAsync()
    {
        try
        {
            var window = App.Current?.ApplicationLifetime is Avalonia.Controls.ApplicationLifetimes.IClassicDesktopStyleApplicationLifetime desktop
                ? desktop.MainWindow
                : null;

            if (window == null) return;

            var files = await window.StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
            {
                Title = "選擇圖片檔案",
                AllowMultiple = false,
                FileTypeFilter = new[]
                {
                    new FilePickerFileType("圖片檔案")
                    {
                        Patterns = new[] { "*.jpg", "*.jpeg", "*.png", "*.bmp" }
                    }
                }
            });

            if (files.Count == 0) return;

            var filePath = files[0].Path.LocalPath;
            await LoadImageInternalAsync(filePath);

            // 建立新樣本
            var sample = new ImageSample
            {
                Id = _nextSampleId++,
                FilePath = filePath,
                Width = (int)ImageWidth,
                Height = (int)ImageHeight
            };

            Samples.Add(sample);
            SelectedSample = sample;

            StatusMessage = $"已新增樣本 #{sample.Id}: {Path.GetFileName(filePath)}";
        }
        catch (Exception ex)
        {
            StatusMessage = $"載入失敗: {ex.Message}";
        }
    }

    /// <summary>
    /// 批次載入多張圖片
    /// </summary>
    [RelayCommand]
    private async Task LoadMultipleImagesAsync()
    {
        try
        {
            var window = App.Current?.ApplicationLifetime is Avalonia.Controls.ApplicationLifetimes.IClassicDesktopStyleApplicationLifetime desktop
                ? desktop.MainWindow
                : null;

            if (window == null) return;

            var files = await window.StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
            {
                Title = "批次選擇圖片檔案",
                AllowMultiple = true,
                FileTypeFilter = new[]
                {
                    new FilePickerFileType("圖片檔案")
                    {
                        Patterns = new[] { "*.jpg", "*.jpeg", "*.png", "*.bmp" }
                    }
                }
            });

            if (files.Count == 0) return;

            int successCount = 0;
            foreach (var file in files)
            {
                var filePath = file.Path.LocalPath;
                
                try
                {
                    // 讀取影像尺寸（不顯示）
                    using var stream = File.OpenRead(filePath);
                    using var bitmap = await Task.Run(() => Bitmap.DecodeToWidth(stream, 100)); // 小尺寸快速讀取

                    var sample = new ImageSample
                    {
                        Id = _nextSampleId++,
                        FilePath = filePath,
                        Width = (int)bitmap.Size.Width,
                        Height = (int)bitmap.Size.Height
                    };

                    Samples.Add(sample);
                    successCount++;
                }
                catch
                {
                    // 略過無法載入的檔案
                    continue;
                }
            }

            if (successCount > 0 && Samples.Count > 0)
            {
                SelectedSample = Samples[0];
                await LoadImageInternalAsync(SelectedSample.FilePath);
                UpdateAnnotationsFromSample();
            }

            StatusMessage = $"批次載入完成: 成功 {successCount} 張，共 {Samples.Count} 個樣本";
        }
        catch (Exception ex)
        {
            StatusMessage = $"批次載入失敗: {ex.Message}";
        }
    }

    /// <summary>
    /// 開始繪製 ROI
    /// </summary>
    [RelayCommand]
    private void StartDrawing(string fieldName)
    {
        if (string.IsNullOrWhiteSpace(fieldName))
        {
            StatusMessage = "請輸入欄位名稱";
            return;
        }

        CurrentFieldName = fieldName;
        StatusMessage = $"請在圖片上拖曳繪製 ROI: {fieldName}";
    }

    /// <summary>
    /// 處理滑鼠按下事件
    /// </summary>
    public void OnMouseDown(double x, double y)
    {
        if (string.IsNullOrEmpty(CurrentFieldName))
        {
            StatusMessage = "請先輸入欄位名稱";
            return;
        }

        IsDrawing = true;
        StartX = x;
        StartY = y;
        CurrentX = x;
        CurrentY = y;
    }

    /// <summary>
    /// 處理滑鼠移動事件
    /// </summary>
    public void OnMouseMove(double x, double y)
    {
        if (IsDrawing)
        {
            CurrentX = x;
            CurrentY = y;
            StatusMessage = $"繪製中... ({StartX:F0}, {StartY:F0}) → ({CurrentX:F0}, {CurrentY:F0})";
        }
    }

    /// <summary>
    /// 處理滑鼠放開事件
    /// </summary>
    public void OnMouseUp(double x, double y)
    {
        if (!IsDrawing) return;

        IsDrawing = false;
        CurrentX = x;
        CurrentY = y;

        // 計算矩形
        var rectX = Math.Min(StartX, CurrentX);
        var rectY = Math.Min(StartY, CurrentY);
        var rectWidth = Math.Abs(CurrentX - StartX);
        var rectHeight = Math.Abs(CurrentY - StartY);

        if (rectWidth < 5 || rectHeight < 5)
        {
            StatusMessage = "ROI 太小，已取消";
            return;
        }

        // 建立標註
        var annotation = new RoiAnnotation
        {
            FieldName = CurrentFieldName!,
            X = (int)rectX,
            Y = (int)rectY,
            Width = (int)rectWidth,
            Height = (int)rectHeight
        };

        Annotations.Add(annotation);

        if (SelectedSample != null)
        {
            SelectedSample.Annotations[CurrentFieldName!] = new PixelRect
            {
                X = (int)rectX,
                Y = (int)rectY,
                Width = (int)rectWidth,
                Height = (int)rectHeight
            };
        }

        StatusMessage = $"已新增 ROI: {CurrentFieldName} ({rectX:F0}, {rectY:F0}, {rectWidth:F0}x{rectHeight:F0})";
        
        // 清空欄位名稱以便繪製下一個
        CurrentFieldName = null;
    }

    /// <summary>
    /// 清除所有標註
    /// </summary>
    [RelayCommand]
    private void ClearAnnotations()
    {
        Annotations.Clear();
        if (SelectedSample != null)
        {
            SelectedSample.Annotations.Clear();
        }
        StatusMessage = "已清除所有標註";
    }

    /// <summary>
    /// 刪除選定的標註
    /// </summary>
    [RelayCommand]
    private void DeleteAnnotation(RoiAnnotation annotation)
    {
        Annotations.Remove(annotation);
        if (SelectedSample != null)
        {
            SelectedSample.Annotations.Remove(annotation.FieldName);
        }
        StatusMessage = $"已刪除標註: {annotation.FieldName}";
    }

    /// <summary>
    /// 樣本選擇變更 - 載入對應影像和標註
    /// </summary>
    partial void OnSelectedSampleChanged(ImageSample? value)
    {
        if (value == null) return;

        // 載入影像
        _ = LoadImageInternalAsync(value.FilePath);

        // 載入標註
        UpdateAnnotationsFromSample();
    }

    /// <summary>
    /// 從當前樣本更新標註列表
    /// </summary>
    private void UpdateAnnotationsFromSample()
    {
        Annotations.Clear();

        if (SelectedSample == null) return;

        foreach (var kvp in SelectedSample.Annotations)
        {
            Annotations.Add(new RoiAnnotation
            {
                FieldName = kvp.Key,
                X = kvp.Value.X,
                Y = kvp.Value.Y,
                Width = kvp.Value.Width,
                Height = kvp.Value.Height
            });
        }
    }

    /// <summary>
    /// 移除樣本
    /// </summary>
    [RelayCommand]
    private void RemoveSample(ImageSample sample)
    {
        Samples.Remove(sample);
        
        if (SelectedSample == sample)
        {
            SelectedSample = Samples.FirstOrDefault();
        }

        StatusMessage = $"已移除樣本 #{sample.Id}";
    }

    /// <summary>
    /// 清除所有樣本
    /// </summary>
    [RelayCommand]
    private void ClearAllSamples()
    {
        Samples.Clear();
        Annotations.Clear();
        CurrentImage = null;
        SelectedSample = null;
        _nextSampleId = 1;
        StatusMessage = "已清除所有樣本";
    }

    /// <summary>
    /// 取得樣本完成度（已標註欄位 / 總欄位數）
    /// </summary>
    public string GetSampleProgress(ImageSample sample)
    {
        if (SelectedProfile == null) return $"{sample.Annotations.Count} 個欄位";
        
        int totalFields = SelectedProfile.Fields.Count;
        int annotatedFields = sample.Annotations.Count;
        
        return $"{annotatedFields}/{totalFields}";
    }

    /// <summary>
    /// 檢查樣本是否完成（所有 Profile 欄位都已標註）
    /// </summary>
    public bool IsSampleComplete(ImageSample sample)
    {
        if (SelectedProfile == null) return false;
        
        var requiredFields = SelectedProfile.Fields.Select(f => f.FieldName).ToHashSet();
        var annotatedFields = sample.Annotations.Keys.ToHashSet();
        
        return requiredFields.IsSubsetOf(annotatedFields);
    }

    /// <summary>
    /// 計算範本統計資料
    /// </summary>
    [RelayCommand]
    private void CalculateTemplateStatistics()
    {
        if (Samples.Count == 0)
        {
            StatusMessage = "沒有樣本可供計算";
            return;
        }

        if (SelectedProfile == null)
        {
            StatusMessage = "請先選擇 Profile";
            return;
        }

        try
        {
            // 使用 TemplateCalculator 計算完整範本
            var template = _templateCalculator.CalculateTemplate(
                Samples.ToList(),
                $"{SelectedProfile.ProfileId}_template",
                $"{SelectedProfile.ProfileName} 範本",
                $"從 {Samples.Count} 個樣本計算產生"
            );

            // 驗證範本品質
            var warnings = _templateCalculator.ValidateQuality(template, threshold: 0.1);

            // 儲存結果
            CalculatedTemplate = template;
            QualityWarnings = warnings;

            // 顯示結果摘要
            var summary = $"範本計算完成！\n";
            summary += $"  樣本數: {template.SamplingMetadata.SampleCount}\n";
            summary += $"  參考尺寸: {template.SamplingMetadata.ReferenceSize.Width}x{template.SamplingMetadata.ReferenceSize.Height}\n";
            summary += $"  欄位數: {template.Regions.Count}\n";
            
            foreach (var (fieldName, region) in template.Regions)
            {
                var stdDevInfo = region.RectStdDev != null
                    ? $"StdDev: X={region.RectStdDev.X:F4}, Y={region.RectStdDev.Y:F4}"
                    : "單一樣本";
                summary += $"    {fieldName}: {stdDevInfo}\n";
            }

            if (warnings.Count > 0)
            {
                summary += $"\n⚠️ 品質警告 ({warnings.Count}):\n";
                summary += string.Join("\n", warnings.Take(5));
                if (warnings.Count > 5)
                    summary += $"\n  ... 還有 {warnings.Count - 5} 個警告";
            }

            StatusMessage = summary;
        }
        catch (Exception ex)
        {
            StatusMessage = $"計算失敗: {ex.Message}";
        }
    }

    /// <summary>
    /// 匯出範本為 JSON 檔案
    /// </summary>
    [RelayCommand]
    private async Task ExportTemplateAsync()
    {
        if (CalculatedTemplate == null)
        {
            StatusMessage = "請先計算範本統計";
            return;
        }

        try
        {
            var window = App.Current?.ApplicationLifetime is Avalonia.Controls.ApplicationLifetimes.IClassicDesktopStyleApplicationLifetime desktop
                ? desktop.MainWindow
                : null;

            if (window == null) return;

            // 開啟儲存檔案對話框
            var file = await window.StorageProvider.SaveFilePickerAsync(new Avalonia.Platform.Storage.FilePickerSaveOptions
            {
                Title = "匯出範本 JSON",
                SuggestedFileName = $"{CalculatedTemplate.TemplateId}.json",
                FileTypeChoices = new[]
                {
                    new Avalonia.Platform.Storage.FilePickerFileType("JSON 檔案")
                    {
                        Patterns = new[] { "*.json" }
                    }
                }
            });

            if (file == null) return;

            // 序列化 TemplateSchema
            var jsonOptions = new System.Text.Json.JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.SnakeCaseLower,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            var json = System.Text.Json.JsonSerializer.Serialize(CalculatedTemplate, jsonOptions);

            // 寫入檔案
            await File.WriteAllTextAsync(file.Path.LocalPath, json);

            // 驗證匯出的範本
            try
            {
                var schemaPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config", "schemas", "template-v1.0.json");
                if (File.Exists(schemaPath))
                {
                    var validator = await RoiSampler.Core.Validation.TemplateSchemaValidator.FromFileAsync(schemaPath);
                    var validationResult = validator.Validate(CalculatedTemplate);

                    if (validationResult.IsValid)
                    {
                        StatusMessage = $"✅ 範本已匯出: {Path.GetFileName(file.Path.LocalPath)}\n驗證通過！";
                    }
                    else
                    {
                        StatusMessage = $"⚠️ 範本已匯出，但驗證發現 {validationResult.Errors.Count} 個問題:\n" +
                                        $"{string.Join("\n", validationResult.Errors.Take(3).Select(e => e.Message))}";
                    }
                }
                else
                {
                    StatusMessage = $"✅ 範本已匯出: {Path.GetFileName(file.Path.LocalPath)}\n(找不到 Schema 檔案，跳過驗證)";
                }
            }
            catch
            {
                // 驗證失敗不影響匯出
                StatusMessage = $"✅ 範本已匯出: {Path.GetFileName(file.Path.LocalPath)}";
            }
        }
        catch (Exception ex)
        {
            StatusMessage = $"匯出失敗: {ex.Message}";
        }
    }

    /// <summary>
    /// 預覽範本 JSON
    /// </summary>
    [RelayCommand]
    private void PreviewTemplate()
    {
        if (CalculatedTemplate == null)
        {
            StatusMessage = "請先計算範本統計";
            return;
        }

        try
        {
            var jsonOptions = new System.Text.Json.JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            var json = System.Text.Json.JsonSerializer.Serialize(CalculatedTemplate, jsonOptions);

            // TODO: 開啟預覽視窗顯示 JSON
            // 目前暫時寫到狀態訊息
            var preview = json.Length > 500 ? json.Substring(0, 500) + "..." : json;
            StatusMessage = $"範本 JSON 預覽 ({json.Length} 字元):\n{preview}";
        }
        catch (Exception ex)
        {
            StatusMessage = $"預覽失敗: {ex.Message}";
        }
    }
}

/// <summary>
/// ROI 標註 (UI 用)
/// </summary>
public class RoiAnnotation
{
    public string FieldName { get; set; } = string.Empty;
    public int X { get; set; }
    public int Y { get; set; }
    public int Width { get; set; }
    public int Height { get; set; }

    public override string ToString() => $"{FieldName}: ({X}, {Y}, {Width}x{Height})";
}

