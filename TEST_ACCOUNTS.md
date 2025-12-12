# Using Google Ads Test Accounts

If your developer token is approved for **test accounts only**, you need to use a Google Ads test customer ID instead of your production account.

## Getting a Test Customer ID

1. **Use Google's Test Account Generator**:
   - Visit: https://developers.google.com/google-ads/api/docs/first-call/test-account-generator
   - Or use the API to generate one programmatically

2. **Common Test Customer IDs** (these may change):
   - Google provides test customer IDs like: `123-456-7890` (example format)
   - Test accounts are free and don't require billing

3. **Update your .env file**:
   ```
   GOOGLE_ADS_CUSTOMER_ID=123-456-7890
   ```
   Replace with your actual test customer ID

## Test Account Limitations

- Test accounts have limited data
- Some features may not be available
- Keyword data may be simulated or limited
- Perfect for development and testing

## Getting Production Access

To use your production account (`814-562-8296`), you need to:

1. **Apply for Production Access**:
   - Go to: https://ads.google.com/ → Tools & Settings → API Center
   - Request production access for your developer token
   - This may require additional verification

2. **Wait for Approval**:
   - Production access can take additional time to approve
   - Google may require more information about your use case

## Quick Test

To test if your setup works with a test account:

1. Get a test customer ID from Google
2. Update `.env` with the test customer ID
3. Run the app - it should work with test accounts

