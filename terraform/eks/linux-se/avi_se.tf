provider "aws" {
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"
  #shared_credentials_file = "${var.aws_creds_file}"
  region     = "${var.aws_region}"
}

data "template_file" "avise" {
  template = "${file("${path.module}/scripts/avise.service")}"
  vars = {
    se_mem_mb      = "${var.se_mem_mb}"
    se_cores       = "${var.se_cores}"
    cloud_uuid     = "${var.avi_cloud}"
    segroup_uuid   = "${var.avi_se_group}"
    se_disk_gb     = "${var.se_disk_gb}"
    avi_controller = "${var.avi_controller}"
    se_docker_tag  = "${var.se_docker_tag}"
  }
}

data "aws_ami" "ubuntu" {
  owners      = ["099720109477"]
  most_recent = true
  filter {
    name      = "virtualization-type"
    values    = ["hvm"]
  }
  filter {
    name      = "name"
    values    = ["ubuntu/images/*ubuntu-xenial-16.04-amd64-server-*"]
  }
  filter {
    name      = "root-device-type"
    values    = ["ebs"]
  }
}

resource "aws_instance" "AviSE" {
  count           = "${var.se_count}"
  ami             = "${data.aws_ami.ubuntu.id}"
  instance_type   = "${var.se_instance_type}"
  subnet_id       = "${element(var.se_subnet, count.index)}"
  key_name        = "${var.ssh_key_name}"
  security_groups = "${var.se_security_groups}"
  associate_public_ip_address = "${var.ec2_public_ip}"

  root_block_device {
    volume_size = "${var.ec2_disk_gb}"
    volume_type = "gp2"
  }

  tags {
    Name = "Avi-SE-${count.index}"
  }
  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = "${file("${var.ssh_key_name}.pem")}"
  } 

  provisioner "file" {
    source      = "${path.module}/scripts/install_dependencies.sh"
    destination = "/home/ubuntu/install_dependencies.sh"
  }

  provisioner "file" {
    content     = "${data.template_file.avise.rendered}"
    destination = "/home/ubuntu/avise.service"
  }
  
  lifecycle {
    ignore_changes = [
      "security_groups",
    ]
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ubuntu/install_dependencies.sh",
      "sudo /home/ubuntu/install_dependencies.sh",
      "sudo mv /home/ubuntu/avise.service /etc/systemd/system/",
      "sudo systemctl daemon-reload",
      "sudo systemctl start avise.service",
      "sudo systemctl enable avise.service",
      "sudo rm -rf /home/ubuntu/*"
    ]
  }
}
