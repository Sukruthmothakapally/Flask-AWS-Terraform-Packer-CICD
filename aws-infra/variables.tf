variable "region" {
  type        = string
  description = "The AWS region in which to create the VPC and networking resources."
}

variable "vpc_name" {
  type        = string
  description = "The name of the VPC to create."
}

variable "vpc_cidr_block" {
  type        = string
  description = "The CIDR block for the VPC."
}

variable "public_subnet_cidr_blocks" {
  type        = list(string)
  description = "A list of CIDR blocks for the public subnets."
}

variable "private_subnet_cidr_blocks" {
  type        = list(string)
  description = "A list of CIDR blocks for the private subnets."
}

variable "availability_zones" {
  type        = list(string)
  description = "A list of availability zones in the specified region."
}

variable "profile" {
  type        = string
  description = "the name of the aws profile to use for authentication"
}

variable "public_route_table_enabled" {
  type    = bool
  default = false
  description = "Indicates whether a public route table should be created or not"
}

variable "private_route_table_enabled" {
  type    = bool
  default = false
  description = "Indicates whether a private route table should be created or not"
}

variable "ami" {
  description = "The ID of the AMI to use for the EC2 instance"
}

variable "instance_type" {
  description = "The type of EC2 instance to launch"
}

variable "key_name" {
  description = "The name of the key pair to use for the EC2 instance"
}

variable "dbpassword" {
  description = "The password for the RDS instance"
}

variable "access_key" {
  type = string
  description = "The access key for the AWS account"
}

variable "secret_key" {
  type = string
  description = "The secret key for the AWS account"
}

variable "engine" {
  type = string
  description = "The name of the database engine to use for the RDS instance"
}
variable "engineversion" {
  type = string
  description = "The version of the database engine to use for the RDS instance"
}
variable "instance" {
  type = string
  description = "The type of RDS instance to launch"
}
variable "identifier" {
  type = string
  description = "The identifier for the RDS instance"
}
variable "username" {
  type = string
  description = "The username to use for the RDS instance"
}
variable "dbname" {
  type = string
  description = "The name of the database to create"
}

variable "hosted_zone_id" {
  type = string
  description = "The ID of the hosted zone for the domain"
}

variable "domain" {
  type        = string
  description = "The domain name to use for the website"
}

variable "certificate" {
  type        = string
  description = "The ARN of the SSL certificate to use for HTTPS"
}

variable "aws_account_id" {
  type = string
  description = "The ID of the AWS account"
}
