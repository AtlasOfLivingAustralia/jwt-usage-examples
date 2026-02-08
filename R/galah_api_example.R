# This R example shows how to generate a JWT and use it when invoking a Galah (common) API.
# Fill Client Id and Gateway API key will be retrieved via api.
# Change authorize and access endpoints according to the environment.

library(httr)
library(jsonlite)

endpoint <- oauth_endpoint(
  authorize = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/authorize",
  access = "https://auth-secure.auth.ap-southeast-2.amazoncognito.com/oauth2/token"
)
app <- oauth_app(
  "galah",
  key = "<<Client Id>>",
  secret = NULL
)

api <- "https://api.test.ala.org.au/common/lists/speciesList"

key_response <- oauth2.0_token(
  endpoint,
  app,
  scope = c("openid","profile","email", "ala/attrs", "ala/roles"),
  type = "application/json",
  use_basic_auth = FALSE,
  config_init = list(),
  client_credentials = FALSE,
  credentials = NULL,
  as_header = TRUE
)

# access_token <- fromJSON(names(key_response$credentials))$access_token
access_token <- key_response$credentials$access_token
string1 <- "Bearer"
string2 <- access_token
header <- paste(string1, string2)

response <- GET("https://api.test.ala.org.au/common/api/getApikey", add_headers(Authorization = header))
apikey <- content(response, type="text", encoding="UTF-8")

api_response <- GET(api, add_headers("x-api-key" = apikey, "Accept"= "application/json", Authorization = header))
print(content(api_response))