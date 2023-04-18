resource "aws_subnet" "public_subnet_1" {
  vpc_id            = aws_vpc.vpc1.id
  cidr_block        = var.public_subnet_cidr_blocks[0]
  availability_zone = var.availability_zones[0]
  tags = {
    Name = "Public Subnet 1"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id            = aws_vpc.vpc1.id
  cidr_block        = var.public_subnet_cidr_blocks[1]
  availability_zone = var.availability_zones[1]
  tags = {
    Name = "Public Subnet 2"
  }
}

resource "aws_subnet" "public_subnet_3" {
  vpc_id            = aws_vpc.vpc1.id
  cidr_block        = var.public_subnet_cidr_blocks[2]
  availability_zone = var.availability_zones[2]
  tags = {
    Name = "Public Subnet 3"
  }
}

resource "aws_subnet" "private_subnet_1" {
  vpc_id            = aws_vpc.vpc1.id
  cidr_block        = var.private_subnet_cidr_blocks[0]
  availability_zone = var.availability_zones[0]
  tags = {
    Name = "Private Subnet 1"
  }
}

resource "aws_subnet" "private_subnet_2" {
  vpc_id            = aws_vpc.vpc1.id
  cidr_block        = var.private_subnet_cidr_blocks[1]
  availability_zone = var.availability_zones[1]
  tags = {
    Name = "Private Subnet 2"
  }
}

resource "aws_subnet" "private_subnet_3" {
  vpc_id            = aws_vpc.vpc1.id
  cidr_block        = var.private_subnet_cidr_blocks[2]
  availability_zone = var.availability_zones[2]
  tags = {
    Name = "Private Subnet 3"
  }
}

resource "aws_db_subnet_group" "rds_subnet_group" {
  name        = "subnet-group"
  description = "Subnet group for RDS instances"

  subnet_ids = [
    aws_subnet.rds_private.id,
    aws_subnet.rds_private2.id,
    aws_subnet.rds_private3.id,
  ]
  tags = {
    Name = "subnet-group"
  }
}

resource "aws_subnet" "rds_private" {
  cidr_block = "10.0.7.0/24"
  vpc_id     = aws_vpc.vpc1.id

  availability_zone = "us-east-2a"

  tags = {
    Name = "private-1"
  }
}

resource "aws_subnet" "rds_private2" {
  cidr_block = "10.0.8.0/24"
  vpc_id     = aws_vpc.vpc1.id

  availability_zone = "us-east-2b"

  tags = {
    Name = "private-2"
  }
}

resource "aws_subnet" "rds_private3" {
  cidr_block = "10.0.9.0/24"
  vpc_id     = aws_vpc.vpc1.id

  availability_zone = "us-east-2c"

  tags = {
    Name = "private-3"
  }
}
