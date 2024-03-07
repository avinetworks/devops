# Avi API Postman Full collection

Prepared by Hugo Xu from VMware Avi Field Engineering</br>

# Introduction

These Postman collections were made out of the corresponding version of Avi controller swagger. The purpose of these collections is to make Avi automation easier. Below are the steps regarding how to use them:

### Import the collection to Postman
- Download and unzip the proper collection version for your Avi controller
- Open Postman and follow the import wizard to import the collection

### Login Avi controller through Postman
- **Disable SSL certificate verification -** If you're using self-signed SSL certificate in the Avi controller, please make sure that you turn off the SSL verification in the Postman settings.

- **Set global variable for controller IP address -** After importing the collection, you will see a list of API folders. Click the top level of these folders, for example, 'Avi_22.1.3', then click "variables" tab, type in your Avi controller IP to replace x.x.x.x for variables "baseUrl" and "Url", and click Save button to save it. The value of X-CSRFToken will be filled out automatically in the next step. Please close the tab of the top folder so that you won't lock those variables for next steps.

- **Login and Retrieve CSRFToken -** 
    - Expand the 0-Login folder and click "Post Login" → Body → form-data → type in the value of username and password. 
    - Click the "Send" button to login your Avi controller. After successfully login, the value of X-CSRFToken will be updated automatically.
    - If not, click "Headers" → "Cookies" → "csrftoken". Select the value and copy it. Back to the top level folder -> "variables" tab -> paste the token value to X-CSRFToken's "Current Value" field, and click save button. You're good to go.

