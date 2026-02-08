# This R example shows how to refresh an access token and use it when invoking an API.
# Set up configs in config.json.

library(httr2)
library(jsonlite)

read_auth_config <- function(path = "config.json") {
  if (!file.exists(path)) stop("Config file not found: ", path)

  cfg <- jsonlite::fromJSON(path, simplifyVector = TRUE)
  cfg
}

refresh_access_token <- function(config_path = "config.json") {
  cfg <- read_auth_config(config_path)

  req <- request(cfg$token_url) |>
      req_timeout(30) |>
      req_headers(Accept = "application/json") |>
      req_body_form(
        grant_type = "refresh_token",
        refresh_token = cfg$refresh_token,
        client_id = cfg$client_id
      )

  if (!is.null(cfg$client_secret) && nzchar(cfg$client_secret)) {
      req <- req |> req_body_form(client_secret = client_secret)
  }

  resp <- req |> req_perform()
  token <- resp_body_json(resp)

  access_token <- token$access_token
  access_token
}

access_token <- refresh_access_token(config_path = "config.json")
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