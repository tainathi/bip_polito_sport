from ctypes import alignment
import constants
import flet as ft
from PhyPhoxControlers import PhyPhoxAppBar
from PhyPhoxChart import PhyPhoxFigure

def main(page: ft.Page):
    
    # trigger callback for updating offset values
    def update_axes_limits(e):
        phyphox_chart.update_y_axes_limits(e.control.value)
    
    # checking for the last ip address written by the user    
    if not page.client_storage.contains_key("ip_address"):
        ip_address = "0.0.0.0"
        port = "8000"
        page.client_storage.set("ip_address",ip_address)
        page.client_storage.set("port",port)
    else:
        ip_address = str(page.client_storage.get("ip_address"))
        port = str(page.client_storage.get("port"))

    phyphox_chart = PhyPhoxFigure()
    phyphox_appbar = PhyPhoxAppBar(ip_address,port,phyphox_chart)

    range_slider = ft.Slider(
                            value=10,
                            min=0,
                            max=constants.slider_minmax_value[phyphox_chart.experiment],
                            width=500,
                            divisions=20,
                            active_color=ft.colors.DEEP_ORANGE_ACCENT,
                            label="{value} " + f"{constants.slider_unit[phyphox_chart.experiment]}",
                            on_change=update_axes_limits
                            )
    
    def dismiss_navigation_drawer(e):
        # phyphox_chart.figure=create_experiment_figure(e.control.selected_index)
        phyphox_chart.experiment=e.control.selected_index
        phyphox_chart.create_update_experiment_figure()
        phyphox_chart.update()
        range_slider.max = constants.slider_minmax_value[phyphox_chart.experiment]
        range_slider.value = constants.slider_initial_value[phyphox_chart.experiment]
        range_slider.label = "{value} " + f"{constants.slider_unit[phyphox_chart.experiment]}"
        e.page.drawer.open=False
        e.page.update()

    # trigger callback for updating offset values
    def update_offset_values(e):
        phyphox_chart.update_offset(phyphox_appbar.running_phyphox)
        
    page.drawer = ft.NavigationDrawer(
        on_change=dismiss_navigation_drawer,
        controls=[
            ft.NavigationDrawerDestination(
                icon=ft.icons.LINEAR_SCALE,
                label=constants.experiments_title[0]
            ),
            ft.NavigationDrawerDestination(
                icon=ft.icons.ROTATE_90_DEGREES_CCW,
                label=constants.experiments_title[1]
            ),
            ft.NavigationDrawerDestination(
                icon=ft.icons.BALANCE_ROUNDED,
                label=constants.experiments_title[2]
            )
        ]
    ) 
            
    page.add(
        phyphox_appbar,
        ft.Row(
            # expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.ElevatedButton(
                    text="Remove offset",
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.DEEP_ORANGE_ACCENT,
                    on_click=update_offset_values
                    ),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10),
                    border=ft.border.all(2, ft.colors.DEEP_ORANGE_ACCENT),
                    border_radius=20,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        controls=[
                            ft.Text(
                                size=18,
                                value="Set axes limits"
                            ),
                            range_slider
                        ]
                    ),
                )
                
            ]
        ),
        phyphox_chart
        
    )

ft.app(main)
