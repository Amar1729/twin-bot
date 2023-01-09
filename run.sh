#! /usr/bin/env bash

set -ex

get_schema () {
    [[ -f schema.py ]] && return

    [[ -z $TOKEN ]] && echo "TOKEN (access token for github) must be set." && exit 1

    python3 -m sgqlc.introspection -H "Authorization: bearer ${TOKEN}" \
        --exclude-deprecated https://api.github.com/graphql schema.json

    sgqlc-codegen schema schema.json schema.py
}

gen_queries () {
    sgqlc-codegen operation --schema schema.json schema operations.py operations.gql
}

get_schema
gen_queries
