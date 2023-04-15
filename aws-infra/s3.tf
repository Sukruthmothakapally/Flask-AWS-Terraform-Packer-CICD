resource "random_pet" "bucket_name" {
  length = 4
}

resource "aws_s3_bucket" "private_bucket" {
  bucket = "my-bucket-${random_pet.bucket_name.id}"
  acl    = "private"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_encryption" {
  bucket = aws_s3_bucket.private_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "s3lifecycle" {
  bucket = aws_s3_bucket.private_bucket.id

  rule {

    id = "30-days-transitioning"

    filter {}

    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
  }
  lifecycle {
    prevent_destroy = false
    ignore_changes  = [rule]
  }
}