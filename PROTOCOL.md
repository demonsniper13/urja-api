# Urja Meter Ops - Protocol Notes

This document summarizes what I learned while exploring the Urja Meter Ops
website and how those findings were used to build the API service.

The investigation was limited to normal logged-in, read-only use of the portal.
No write operations were performed.

## Website overview

Urja Meter Ops is a web application used to view smart-meter information.

From the browser traffic, I found that the website does not require browser
automation for every operation. The frontend makes HTTP requests in the
background to retrieve meter, transformer, location and energy information.

This was useful because the new API service could communicate with those
HTTP endpoints directly instead of running a browser for every API request.

The frontend appears to be built with SvelteKit, and authentication uses a
Better Auth session cookie.

## How I investigated the portal

I first used the website normally in a browser and observed its network
traffic.

I used Playwright to record a HAR file while navigating the portal. The HAR
helped identify which HTTP requests were made when logging in and viewing
different types of meter data.

I then used a small Python/httpx script to repeat the useful requests outside
the browser.

This confirmed that a browser was not required at runtime once the login and
request behavior were understood.

One request, the bulk meter export, required additional signing headers. I
inspected the frontend JavaScript involved in that request and reproduced the
same signing calculation in Python.

The final API service uses these findings through a normal HTTP client rather
than through Playwright.

## Authentication

The portal uses a normal login form.

The login request is made using:

`POST /login`

with the email and password sent as form data.

The request also needs the portal's `Origin` header.

After a successful login, the portal creates a session cookie named:

`__Secure-better-auth.session_token`

The API client keeps this cookie and automatically sends it with later portal
requests.

I found that checking only the final HTTP status is not a reliable way of
confirming login. The HTTP client may follow redirects and end on a page that
returns `200`.

For this reason, the API checks that the session cookie was actually created.

If the portal later returns `401`, the API treats the session as expired,
clears the old session information and logs in again.

## Meter data

The portal provides meter information containing fields such as:

- meter ID
- serial number
- manufacturer
- phase type
- installation status
- installation type
- build/version
- transformer code
- network hierarchy
- location

During investigation I found 403 meters in the dataset.

The hierarchy attached to a meter includes information for:

- zone
- circle
- division
- subdivision
- substation
- feeder
- distribution transformer

This hierarchy is preserved by the new API rather than being discarded.

## Meter search

While using the portal, I observed a meter search request under the portal
routes.

The search behavior I tested matched meter IDs and serial numbers and was
case-insensitive.

Searching using a transformer code did not behave like a meter-ID or serial
search.

Because the bulk meter dataset was available, the new API does not depend on
the portal search for its filtering features.

Instead, it retrieves the meter dataset and supports its own filters for
attributes such as manufacturer, status, phase, build, feeder and transformer.

## Transformer data

The portal also exposes distribution-transformer data.

The transformer records I observed contained information such as:

- transformer code
- transformer name
- feeder code
- capacity

The transformer data was paginated.

I found 40 transformers during the investigation.

I did not observe a useful transformer search capability in the portal, so
transformer searching in the new API is performed locally.

The meter data contains a transformer code, which also made it possible to
link meters to their corresponding transformer in the new service.

## Meter location

The portal provides location information for individual meters.

One inconsistency I noticed was that location information does not always use
the same representation.

In the bulk meter data, coordinates are numeric values named:

`lat`
`lng`

The dedicated meter location response uses:

`latitude`
`longitude`

and the values are strings.

I also observed a precision difference for one v2 meter: the detailed location
contained more decimal places than the location in the bulk data.

I did not test enough v2 meters to conclude that this always happens.

For this reason, the new API uses the bulk coordinates when returning meter
lists and uses the dedicated location data when returning a single meter.

The API normalizes both formats into:

```json
{
  "lat": 26.93,
  "lng": 75.83
}