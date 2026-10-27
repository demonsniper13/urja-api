# Urja Meter Ops protocol notes

These notes describe the portal behavior observed through normal logged-in use and read-only HTTP requests.

## Application and authentication

The frontend appears to be SvelteKit and uses a Better Auth session cookie.

Login is a form-encoded `POST /login` with `email` and `password`. The request needs the portal `Origin` header. A successful HTTP status alone is not a reliable login check because redirects may be followed. The client therefore checks for `__Secure-better-auth.session_token`.

Requests without a valid session return `401`.

## Data endpoints

### Meter search

`GET /portal/meters/search?q=&page=N`

Returns `data`, `total`, `page` and `pageSize`. Search is case-insensitive and matches text inside meter ID or serial number. It did not match transformer code during investigation.

### Transformers

`GET /portal/dts?page=N`

Returns transformer code, name, feeder code and capacity. The endpoint is paginated and has no observed search parameter.

### Meter geo

`GET /portal/meters/{id}/geo`

Returns `latitude` and `longitude` as strings. The bulk export instead returns numeric `lat` and `lng`. A v2 sample returned more decimal precision from this endpoint than from the export.

### Meter energy

`GET /portal/meters/{id}/energy`

Returns readings containing `timestamp`, `kwh`, `kvah` and `voltR`. Values are strings. Timestamps use `DD/MM/YYYY HH:mm` and do not include a timezone. kWh and kVAh appear to be cumulative totals.

### Signing key

`GET /portal/keys`

Returns the export signing secret to a logged-in user. This weakens the security value of signing because the same user who calls the export can retrieve its key.

### Bulk export

`GET /portal/export?page=1`

The browser signs this request. The observed signing input was:

```text
GET\n/portal/export\npage=1\n<unix_seconds>
```

The signature is the lowercase hexadecimal HMAC-SHA256 digest using the portal-provided signing secret. It is sent in `x-signature`; the timestamp is sent in `x-timestamp`. The signature must be produced with a fresh timestamp.

Although the request includes `page=1`, the observed response returned the full meter dataset in one call. The API service uses this as its local query source.

## Errors

Unknown meter IDs on geo or energy returned a `404` response with a not-found error. Missing or invalid export signatures returned `401`.

## Data quirks

- Export geo values are numeric; the dedicated geo endpoint returns strings.
- Energy values are strings and timestamps omit timezone information.
- The export and detailed geo endpoint may use different coordinate precision.
- Serial-number prefixes should not be treated as a reliable manufacturer identifier.
- The export contains hierarchy data down to feeder and distribution transformer.

## Security handling

Credentials are loaded from `.env`. The repository must not contain the portal password, signing secret, session cookie or HAR capture. The service keeps the signing secret only in memory for the current session.
