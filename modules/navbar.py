import dash_bootstrap_components as dbc

def Navbar():
     navbar = dbc.NavbarSimple(
         children=[
             dbc.NavItem(dbc.NavLink("Documentation", href="/documentation")),
          ],
          expand="lg",
          brand="Home",
          brand_href="/",
          sticky="top",
          brand_external_link=True,
          color = "dark",
          dark = True
        )
     return navbar
