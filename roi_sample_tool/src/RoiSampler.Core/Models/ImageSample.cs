namespace RoiSampler.Core.Models;

/// <summary>
/// 圖片樣本
/// </summary>
public class ImageSample
{
    public int Id { get; set; }
    public string FilePath { get; set; } = string.Empty;
    public int Width { get; set; }
    public int Height { get; set; }
    public Dictionary<string, PixelRect> Annotations { get; set; } = new();
}

/// <summary>
/// 像素座標矩形
/// </summary>
public class PixelRect
{
    public int X { get; set; }
    public int Y { get; set; }
    public int Width { get; set; }
    public int Height { get; set; }

    public RectRatio ToRatio(int imageWidth, int imageHeight)
    {
        return RectRatio.FromPixels(X, Y, Width, Height, imageWidth, imageHeight);
    }
}
