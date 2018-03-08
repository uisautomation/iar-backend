#!/usr/bin/env bash
#
# Use Hydra command line client to create a test client application.
#
# For UI testing, create "testclient" capable of requesting the scope required
# to access the IAR API.
#
# For the backend itself, create a client, "iarbackend", capable of requesting
# hydra.introspect and lookup:anonymous scopes.
#
set -xe

# A convenient alias for calling hydra
function hydra() {
	docker-compose exec hydra hydra $@
}

# Delete any existing clients. It is OK for these calls to fail if the
# corresponding clients did not exist
hydra clients delete testclient || echo "-- testclient not deleted"
hydra clients delete iarbackend || echo "-- iarbackend not deleted"

# Create testclient client which can use implicit flow to log into web-based
# UIs. It is a "public" client (i.e. one with no secret) and as such can *only*
# use the implicit  flow
hydra clients create \
    --id testclient --is-public \
    --grant-types implicit \
    --response-types token,code,refresh_token \
    --callbacks http://localhost:4445/callback,http://localhost:8000/static/iarbackend/oauth2-redirect.html,http://localhost:8080/static/lookupproxy/oauth2-redirect.html,http://localhost:3000/oauth2-callback \
    --allowed-scopes lookup:anonymous,assetregister

# Create iarbackend client which can request scopes to access the lookup proxy
# and to introspect tokens from hydra.
hydra clients create \
    --id iarbackend --secret backendsecret \
    --grant-types client_credentials \
    --response-types token \
    --allowed-scopes lookup:anonymous,hydra.introspect

# We need to create a Hydra policy allowing the backend to introspect tokens.
# Delete a policy if it is already in place and re-create it
hydra policies delete introspect-policy \
	|| echo "-- introspect-policy not deleted"

hydra policies create --actions introspect \
	--description "Allow all clients with hydra.introspect to instrospect" \
	--allow \
	--id introspect-policy \
	--resources "rn:hydra:oauth2:tokens" \
	--subjects "<.*>"
