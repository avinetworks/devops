1. Copy ec2_ssh_key.pem file to this directory
2. Edit variables.tf and fill in values for the variables, according to the comments for each variable
3. Export AWS key and secret
     $ export AWS_ACCESS_KEY_ID="anaccesskey"
     $ export AWS_SECRET_ACCESS_KEY="asecretkey"
4. Run
     $ terraform apply

5. Destroy
     $ terraform 
