# This R example shows how to generate an OIDC access token (often a JWT) using client credential method.
# Set up configs in config.json.

library(httr2)
library(jsonlite)

read_auth_config <- function(path = "config.json") {
  if (!file.exists(path)) stop("Config file not found: ", path)

  cfg <- jsonlite::fromJSON(path, simplifyVector = TRUE)
  cfg
}

retrieve_new_access_token <- function(config_path = "config.json") {
  cfg <- read_auth_config(config_path)

  req <- request(cfg$token_url) |>
      req_timeout(30) |>
      req_headers(Accept = "application/json",`Content-Type` = "application/x-www-form-urlencoded") |>
      req_auth_basic(cfg$client_id, cfg$client_secret) |>
      req_body_form(
        grant_type = "client_credentials"
      )
  req <- req |> req_body_form(scope = cfg$scope)
  resp <- req |> req_perform()

  token <- resp_body_json(resp)

  access_token <- token$access_token
  access_token
}

access_token <- retrieve_new_access_token(config_path = "config.json")
print(access_token)