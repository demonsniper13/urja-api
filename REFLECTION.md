# Reflection

## Assumptions

I assumed the energy timestamps represent Indian Standard Time because the portal does not attach a timezone. I also treated kWh as a cumulative reading, based on the sequence observed in the data. Both choices are visible in the API behavior and documented rather than hidden.

## Hardest part

The hardest part was understanding the bulk export because it did not behave like the simpler read endpoints. I recorded normal browser traffic, found the headers used by the export and then inspected the downloaded frontend JavaScript to understand how the signature was built. I reproduced the HMAC calculation in a small script and compared it with a browser request before putting it into the API client.

## If I had another day

I would add mocked integration tests for login expiry, retry behavior and upstream error mapping. I would also check more v2 meters to understand whether their location rounding is consistent, and add a small data-quality indicator for counter resets instead of representing them only with a null consumption value.

## A mistake I made

I first tried to treat the export like a normal paginated endpoint. Investigation showed that `page=1` returned the complete dataset and required a signature. That changed the design: the service now fetches it once, caches it briefly and performs simple filtering locally.

## Self-criticism

The cache is local to one process and there is no durable snapshot when the portal is unavailable. The health endpoint also makes a live portal request, so repeated health checks create upstream traffic. These choices keep the take-home implementation small, but I would revisit them before production use.
