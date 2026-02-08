# This R example shows how to generate an OIDC access token (often a JWT) using Authorization Code + PKCE and use it when invoking an API.
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

  client <- oauth_client(
    id = cfg$client_id,
    token_url = cfg$token_url
  )

  # PKCE auth code flow (interactive browser login)
  token <- oauth_flow_auth_code(
    client = client,
    auth_url = cfg$authorize_url,
    pkce = TRUE,
    scope = paste(strsplit(cfg$scopes, "\\s+")[[1]], collapse = " "),
    redirect_uri = cfg$redirect_uri
  )

  access_token <- token$access_token
  access_token
}

access_token <- retrieve_new_access_token(config_path = "config.json")
string1 <- "Bearer"
string2 <- access_token
header <- paste(string1, string2)

api <- "https://api.ala.org.au/occurrences/config"

api_response <- request(api) |>
  req_headers(
    Accept = "application/json",
    Authorization = header
  ) |>
  req_perform()
print(resp_body_json(api_response))