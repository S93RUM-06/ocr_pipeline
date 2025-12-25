using NJsonSchema;
using RoiSampler.Core.Models;
using System.Text.Json;

namespace RoiSampler.Core.Validation
{
    /// <summary>
    /// 驗證 TemplateSchema 是否符合 JSON Schema 定義及業務邏輯
    /// </summary>
    public class TemplateSchemaValidator
    {
        private readonly JsonSchema _schema;

        /// <summary>
        /// 從 JSON Schema 檔案載入驗證器
        /// </summary>
        /// <param name="schemaFilePath">JSON Schema 檔案路徑</param>
        public static async Task<TemplateSchemaValidator> FromFileAsync(string schemaFilePath)
        {
            if (!File.Exists(schemaFilePath))
            {
                throw new FileNotFoundException($"Schema file not found: {schemaFilePath}");
            }

            var schemaJson = await File.ReadAllTextAsync(schemaFilePath);
            var schema = await JsonSchema.FromJsonAsync(schemaJson);
            return new TemplateSchemaValidator(schema);
        }

        /// <summary>
        /// 從 JSON Schema 字串建立驗證器
        /// </summary>
        public static async Task<TemplateSchemaValidator> FromSchemaAsync(string schemaJson)
        {
            var schema = await JsonSchema.FromJsonAsync(schemaJson);
            return new TemplateSchemaValidator(schema);
        }

        private TemplateSchemaValidator(JsonSchema schema)
        {
            _schema = schema ?? throw new ArgumentNullException(nameof(schema));
        }

        /// <summary>
        /// 驗證 TemplateSchema 物件
        /// </summary>
        public ValidationResult Validate(TemplateSchema template)
        {
            if (template == null)
            {
                return ValidationResult.Failure("Template is null");
            }

            var errors = new List<ValidationError>();

            // 1. JSON Schema 驗證
            var json = JsonSerializer.Serialize(template, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
                WriteIndented = true
            });

            var schemaErrors = _schema.Validate(json);
            if (schemaErrors.Any())
            {
                errors.AddRange(schemaErrors.Select(e => new ValidationError
                {
                    ErrorType = ValidationErrorType.SchemaViolation,
                    Path = e.Path ?? string.Empty,
                    Message = e.ToString()
                }));
            }

            // 2. 業務邏輯驗證
            ValidateBusinessRules(template, errors);

            return errors.Count == 0
                ? ValidationResult.Success()
                : ValidationResult.Failure(errors);
        }

        /// <summary>
        /// 驗證業務邏輯規則
        /// </summary>
        private void ValidateBusinessRules(TemplateSchema template, List<ValidationError> errors)
        {
            // 2.1 template_id 不可為空
            if (string.IsNullOrWhiteSpace(template.TemplateId))
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.BusinessRule,
                    Path = "template_id",
                    Message = "template_id cannot be empty"
                });
            }

            // 2.2 必須至少有一個 region
            if (template.Regions == null || template.Regions.Count == 0)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.BusinessRule,
                    Path = "regions",
                    Message = "At least one region is required"
                });
                return; // 後續驗證依賴 regions
            }

            // 2.3 驗證每個 region
            foreach (var kvp in template.Regions)
            {
                var fieldName = kvp.Key;
                var region = kvp.Value;
                var regionPath = $"regions.{fieldName}";

                // 驗證座標範圍 [0, 1]
                ValidateRectRatio(region.RectRatio, $"{regionPath}.rect_ratio", errors);

                // 驗證標準差範圍 [0, 1]（如果存在）
                if (region.RectStdDev != null)
                {
                    ValidateRectStdDev(region.RectStdDev, $"{regionPath}.rect_std_dev", errors);
                }

                // 驗證資料類型
                if (!IsValidDataType(region.DataType))
                {
                    errors.Add(new ValidationError
                    {
                        ErrorType = ValidationErrorType.BusinessRule,
                        Path = $"{regionPath}.data_type",
                        Message = $"Invalid data_type: {region.DataType}. Must be one of: text, number, date, barcode, qrcode"
                    });
                }
            }

            // 2.4 驗證 sampling_metadata
            if (template.SamplingMetadata != null)
            {
                ValidateSamplingMetadata(template.SamplingMetadata, "sampling_metadata", errors);
            }
        }

        /// <summary>
        /// 驗證 RectRatio 座標範圍
        /// </summary>
        private void ValidateRectRatio(RectRatio rect, string path, List<ValidationError> errors)
        {
            if (rect == null)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.BusinessRule,
                    Path = path,
                    Message = "rect_ratio cannot be null"
                });
                return;
            }

            // 檢查範圍 [0, 1]
            if (rect.X < 0 || rect.X > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateRange,
                    Path = $"{path}.x",
                    Message = $"x must be in range [0, 1], got {rect.X}"
                });
            }

            if (rect.Y < 0 || rect.Y > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateRange,
                    Path = $"{path}.y",
                    Message = $"y must be in range [0, 1], got {rect.Y}"
                });
            }

            if (rect.Width < 0 || rect.Width > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateRange,
                    Path = $"{path}.width",
                    Message = $"width must be in range [0, 1], got {rect.Width}"
                });
            }

            if (rect.Height < 0 || rect.Height > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateRange,
                    Path = $"{path}.height",
                    Message = $"height must be in range [0, 1], got {rect.Height}"
                });
            }

            // 檢查邏輯：右下角不可超出邊界
            if (rect.X + rect.Width > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateLogic,
                    Path = $"{path}",
                    Message = $"x + width ({rect.X} + {rect.Width} = {rect.X + rect.Width}) exceeds 1.0"
                });
            }

            if (rect.Y + rect.Height > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateLogic,
                    Path = $"{path}",
                    Message = $"y + height ({rect.Y} + {rect.Height} = {rect.Y + rect.Height}) exceeds 1.0"
                });
            }

            // 檢查非零面積
            if (rect.Width <= 0 || rect.Height <= 0)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateLogic,
                    Path = $"{path}",
                    Message = "width and height must be greater than 0"
                });
            }
        }

        /// <summary>
        /// 驗證 RectStdDev 標準差範圍
        /// </summary>
        private void ValidateRectStdDev(RectStdDev stdDev, string path, List<ValidationError> errors)
        {
            if (stdDev.X < 0 || stdDev.X > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateRange,
                    Path = $"{path}.x",
                    Message = $"x_std_dev must be in range [0, 1], got {stdDev.X}"
                });
            }

            if (stdDev.Y < 0 || stdDev.Y > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateRange,
                    Path = $"{path}.y",
                    Message = $"y_std_dev must be in range [0, 1], got {stdDev.Y}"
                });
            }

            if (stdDev.Width < 0 || stdDev.Width > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateRange,
                    Path = $"{path}.width",
                    Message = $"width_std_dev must be in range [0, 1], got {stdDev.Width}"
                });
            }

            if (stdDev.Height < 0 || stdDev.Height > 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.CoordinateRange,
                    Path = $"{path}.height",
                    Message = $"height_std_dev must be in range [0, 1], got {stdDev.Height}"
                });
            }
        }

        /// <summary>
        /// 驗證 SamplingMetadata
        /// </summary>
        private void ValidateSamplingMetadata(SamplingMetadata metadata, string path, List<ValidationError> errors)
        {
            if (metadata.SampleCount < 1)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.BusinessRule,
                    Path = $"{path}.sample_count",
                    Message = $"sample_count must be >= 1, got {metadata.SampleCount}"
                });
            }

            if (metadata.ReferenceSize.Width <= 0)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.BusinessRule,
                    Path = $"{path}.reference_size.width",
                    Message = $"reference_size.width must be > 0, got {metadata.ReferenceSize.Width}"
                });
            }

            if (metadata.ReferenceSize.Height <= 0)
            {
                errors.Add(new ValidationError
                {
                    ErrorType = ValidationErrorType.BusinessRule,
                    Path = $"{path}.reference_size.height",
                    Message = $"reference_size.height must be > 0, got {metadata.ReferenceSize.Height}"
                });
            }
        }

        /// <summary>
        /// 檢查資料類型是否有效
        /// </summary>
        private bool IsValidDataType(string dataType)
        {
            var validTypes = new[] { "string", "number", "date", "datetime", "phone", "email", "tax_id", "custom" };
            return validTypes.Contains(dataType, StringComparer.OrdinalIgnoreCase);
        }
    }

    /// <summary>
    /// 驗證結果
    /// </summary>
    public class ValidationResult
    {
        public bool IsValid { get; init; }
        public List<ValidationError> Errors { get; init; } = new();

        public static ValidationResult Success() => new() { IsValid = true };

        public static ValidationResult Failure(string message)
        {
            return new()
            {
                IsValid = false,
                Errors = new List<ValidationError>
                {
                    new() { Message = message, ErrorType = ValidationErrorType.General }
                }
            };
        }

        public static ValidationResult Failure(List<ValidationError> errors)
        {
            return new()
            {
                IsValid = false,
                Errors = errors
            };
        }

        /// <summary>
        /// 格式化錯誤訊息
        /// </summary>
        public string GetErrorMessage()
        {
            if (IsValid) return "Validation passed";

            return string.Join("\n", Errors.Select(e =>
                string.IsNullOrEmpty(e.Path)
                    ? $"[{e.ErrorType}] {e.Message}"
                    : $"[{e.ErrorType}] {e.Path}: {e.Message}"));
        }
    }

    /// <summary>
    /// 驗證錯誤
    /// </summary>
    public class ValidationError
    {
        public ValidationErrorType ErrorType { get; init; }
        public string Path { get; init; } = string.Empty;
        public string Message { get; init; } = string.Empty;
    }

    /// <summary>
    /// 錯誤類型
    /// </summary>
    public enum ValidationErrorType
    {
        General,
        SchemaViolation,
        BusinessRule,
        CoordinateRange,
        CoordinateLogic
    }
}
