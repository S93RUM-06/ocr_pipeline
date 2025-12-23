using Avalonia.Controls;
using RoiSampler.App.ViewModels;

namespace RoiSampler.App.Views;

public partial class ProfileManagerWindow : Window
{
    public ProfileManagerWindow()
    {
        InitializeComponent();
        DataContext = new ProfileManagerViewModel();
    }
}
