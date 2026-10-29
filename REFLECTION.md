# Reflection

## What assumptions did I make?

The main assumption I made was around the energy data.

The portal returns timestamps without any timezone information, so I assumed IST (`+05:30`) when converting them to ISO timestamps in the API.

I also treated the kWh values as cumulative readings because that matched the pattern I observed in the returned data. Based on this, the API calculates `consumption_kwh` as the difference between consecutive readings.

Since these behaviors were not explicitly documented by the portal, I kept them as documented assumptions rather than treating them as confirmed rules. The normalization logic is also kept simple so these decisions can be changed easily if more information becomes available.

## What was the most difficult part, and how did I get unstuck?

The most difficult part was understanding the bulk meter export.

Most of the portal data could be retrieved through normal authenticated requests, but the export request required additional signature and timestamp headers.

I first captured the browser network traffic and compared the export request with the other portal requests. After identifying the additional headers, I inspected the relevant frontend JavaScript to understand how the signature was generated.

I then reproduced the HMAC-SHA256 calculation in a small Python script and compared the generated signature with the one sent by the browser. Once they matched, I was able to reproduce the export request using `httpx` without requiring browser automation.

This was also an important design discovery because the export returned the complete meter dataset, which made simple local searching and filtering practical.

## If I had another day, what would I improve?

My first priority would be improving reliability and visibility into problems with the upstream portal.

I would add better monitoring around portal response times, upstream failures and cache freshness. The current health endpoint checks whether the portal is reachable, but additional information would make it easier to understand whether a problem is caused by the portal, authentication or stale data.

I would also move meter and transformer refreshes into a small background process rather than waiting for an API request to trigger a refresh. I would keep the last successful snapshot available so that temporary portal downtime does not immediately prevent dataset-based API requests from working.

Finally, I would expand the automated tests around the upstream client, especially expired sessions, login failures, portal timeouts, malformed responses, pagination, cache expiry and the public API error responses.

After those reliability improvements, additional functionality such as daily energy summaries or location-based meter filtering would be useful extensions.

## What mistake did I make while solving this?

One mistake I made was initially treating the bulk export like a normal paginated endpoint.

I expected `page=1` to return only the first page of meter data, so I initially spent more time looking at the normal meter search and pagination flow.

During testing I found that the export request behaved differently: it required a signed request and, in the behavior I observed, `page=1` returned the complete meter dataset.

Once I understood the signing mechanism and successfully reproduced the export request, I changed the design to use the bulk export as a short-lived local dataset and perform searching, filtering and pagination inside the API service.

I also focused first on getting the main successful flows working. Looking back, I would have tested failure cases such as expired sessions, portal timeouts and unexpected upstream responses earlier. That would have helped shape the retry and error-handling behavior sooner.

## If I were reviewing my own submission, what would I criticize?

The biggest limitation is that the cache exists only inside the application process.

For the current dataset and a small single-process service, this keeps the implementation simple. However, it would not be a good long-term solution if the service needed multiple application instances, larger datasets or stronger availability guarantees.

The automated test suite is also intentionally small. It covers some important normalization, energy and signing behavior, but the upstream client would benefit from more mocked tests around authentication, session expiry, retries and portal failures.

There are also a few areas where the API has to make assumptions because the portal does not provide enough information, particularly the energy timezone and how to interpret a decrease in cumulative kWh readings.

I chose to keep those limitations visible and documented rather than adding complexity or pretending the upstream system provides information that it does not.