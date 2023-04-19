resource "aws_db_parameter_group" "mysql" {
  name        = "mysql-parameters"
  family      = "mysql8.0"
  description = "Custom MySQL parameter group"

  parameter {
    name  = "max_connections"
    value = "1000"
  }
}

resource "aws_db_instance" "csye6225db" {
  allocated_storage    = 10
  engine               = var.engine
  engine_version       = var.engineversion
  instance_class       = var.instance
  identifier           = var.identifier
  username             = var.username
  password             = var.dbpassword
  parameter_group_name = aws_db_parameter_group.mysql.name
  db_subnet_group_name = aws_db_subnet_group.rds_subnet_group.name
  publicly_accessible  = false
  multi_az             = false
  db_name              = var.dbname
  skip_final_snapshot  = true

  vpc_security_group_ids = [
    aws_security_group.rds_sg.id
  ]

  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds_encrypt.arn

}
