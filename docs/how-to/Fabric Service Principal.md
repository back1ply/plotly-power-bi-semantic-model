**Set up Azure Service Principal**

1. Get your Azure client ID
    1. Go to [portal.azure.com](http://portal.azure.com/)
    2. Search bar \- “app registrations”
    3. Click on New registration —\> give it a name and register, keep the defaults. (remember the name you gave it)
    4. Copy into a notepad your application (client) ID. This is your client ID that you will need to provide to Plotly Studio when connecting to your data
2. Get your Azure client secret
    1. Go to sidebar of the App registrations —\> click Manage —\> Certificates & secrets
    2. Click New client secret
    3. Copy into a notepad the Value (not the Secret ID). The Value number is actually the Client secret value that you will need to provide to Plotly Studio when connecting to your data
3. Make the workspace aware of your Azure service principal
    1. Go back to your workspace in Power BI online and click “Manage access” in the top right corner
    2. Click “Add people or groups” and add your app registration name. Give it a member access
4. Allow your service principal to call Fabric public APIs
    1. Go to the Power BI Setting button at the very top of the page and click “Admin Portal”
    2. Inside “Tenant settings” find the “Developer settings” section and open the “Service principals can call Fabric public APIs”. Have it enabled for the entire organization.
5. Go to Plotly Studio and create a new project. And enter this prompt to connect Power BI semantic model to Plotly Studio.

   *Connect to PowerBi services and the “Superstore Sales Analysis” semantic model in the “test-workspace-1”. Show the “fact\_sales”* *table.*

   *For authentication, use only these credentials:*

   *tenantID*

   *client secret value*

   *client application ID*

   *Try this as scope: https://analysis.windows.net/powerbi/api/.default \- not https://api.powerbi.com*

   *Include comprehensive error handling and diagnostic reporting in the code.*

   *Do not try to use or install the azure library.*
