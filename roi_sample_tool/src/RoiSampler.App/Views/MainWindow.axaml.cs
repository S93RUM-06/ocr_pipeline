using Avalonia.Controls;
using Avalonia.Input;
using RoiSampler.App.ViewModels;

namespace RoiSampler.App.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        
        // 連接 Canvas 事件到 ViewModel
        ImageCanvas.PointerPressed += OnCanvasPointerPressed;
        ImageCanvas.PointerMoved += OnCanvasPointerMoved;
        ImageCanvas.PointerReleased += OnCanvasPointerReleased;
    }

    private void OnCanvasPointerPressed(object? sender, PointerEventArgs e)
    {
        if (DataContext is MainWindowViewModel vm)
        {
            var point = e.GetPosition(ImageCanvas);
            vm.OnMouseDown(point.X, point.Y);
        }
    }

    private void OnCanvasPointerMoved(object? sender, PointerEventArgs e)
    {
        if (DataContext is MainWindowViewModel vm)
        {
            var point = e.GetPosition(ImageCanvas);
            vm.OnMouseMove(point.X, point.Y);
        }
    }

    private void OnCanvasPointerReleased(object? sender, PointerEventArgs e)
    {
        if (DataContext is MainWindowViewModel vm)
        {
            var point = e.GetPosition(ImageCanvas);
            vm.OnMouseUp(point.X, point.Y);
        }
    }
}
