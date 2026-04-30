resource "aws_dynamodb_table" "cost_table" {
  name         = "cost_table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "date"

  attribute {
    name = "date"
    type = "S"
  }
}
