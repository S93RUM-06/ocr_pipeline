using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using System;

namespace RoiSampler.App.Controls;

/// <summary>
/// 支援 ROI 繪製的圖片 Canvas
/// </summary>
public class RoiCanvas : Control
{
    public static readonly StyledProperty<Bitmap?> ImageProperty =
        AvaloniaProperty.Register<RoiCanvas, Bitmap?>(nameof(Image));

    public static readonly StyledProperty<bool> IsDrawingProperty =
        AvaloniaProperty.Register<RoiCanvas, bool>(nameof(IsDrawing));

    public static readonly StyledProperty<double> StartXProperty =
        AvaloniaProperty.Register<RoiCanvas, double>(nameof(StartX));

    public static readonly StyledProperty<double> StartYProperty =
        AvaloniaProperty.Register<RoiCanvas, double>(nameof(StartY));

    public static readonly StyledProperty<double> CurrentXProperty =
        AvaloniaProperty.Register<RoiCanvas, double>(nameof(CurrentX));

    public static readonly StyledProperty<double> CurrentYProperty =
        AvaloniaProperty.Register<RoiCanvas, double>(nameof(CurrentY));

    public Bitmap? Image
    {
        get => GetValue(ImageProperty);
        set => SetValue(ImageProperty, value);
    }

    public bool IsDrawing
    {
        get => GetValue(IsDrawingProperty);
        set => SetValue(IsDrawingProperty, value);
    }

    public double StartX
    {
        get => GetValue(StartXProperty);
        set => SetValue(StartXProperty, value);
    }

    public double StartY
    {
        get => GetValue(StartYProperty);
        set => SetValue(StartYProperty, value);
    }

    public double CurrentX
    {
        get => GetValue(CurrentXProperty);
        set => SetValue(CurrentXProperty, value);
    }

    public double CurrentY
    {
        get => GetValue(CurrentYProperty);
        set => SetValue(CurrentYProperty, value);
    }

    public new event EventHandler<PointerPressedEventArgs>? PointerPressed;
    public new event EventHandler<PointerEventArgs>? PointerMoved;
    public new event EventHandler<PointerReleasedEventArgs>? PointerReleased;

    static RoiCanvas()
    {
        AffectsRender<RoiCanvas>(
            ImageProperty,
            IsDrawingProperty,
            StartXProperty,
            StartYProperty,
            CurrentXProperty,
            CurrentYProperty);
    }

    protected override void OnPointerPressed(PointerPressedEventArgs e)
    {
        base.OnPointerPressed(e);
        PointerPressed?.Invoke(this, e);
    }

    protected override void OnPointerMoved(PointerEventArgs e)
    {
        base.OnPointerMoved(e);
        PointerMoved?.Invoke(this, e);
    }

    protected override void OnPointerReleased(PointerReleasedEventArgs e)
    {
        base.OnPointerReleased(e);
        PointerReleased?.Invoke(this, e);
    }

    public override void Render(DrawingContext context)
    {
        base.Render(context);

        // 繪製圖片
        if (Image != null)
        {
            context.DrawImage(Image, new Rect(0, 0, Image.Size.Width, Image.Size.Height));
        }

        // 繪製當前 ROI（如果正在繪製）
        if (IsDrawing)
        {
            var x = Math.Min(StartX, CurrentX);
            var y = Math.Min(StartY, CurrentY);
            var width = Math.Abs(CurrentX - StartX);
            var height = Math.Abs(CurrentY - StartY);

            var rect = new Rect(x, y, width, height);
            var pen = new Pen(Brushes.Red, 2);
            var fillBrush = new SolidColorBrush(Colors.Red, 0.2);

            context.DrawRectangle(fillBrush, pen, rect);
        }
    }
}
