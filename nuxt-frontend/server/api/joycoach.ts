export default defineEventHandler(async (event) => {
    const runtimeConfig = useRuntimeConfig();
    const body = await readBody(event);
    
    console.log('body', body);


    // Assuming `message` is a field in your `body`
    const message = body.message;

    // If message is empty, return 400
    if (!message) {
      event.res.statusCode = 400;
      return { error: 'Message is required' };
    }

    try {
      const apiResponse = await $fetch(`${runtimeConfig.private.BACKEND_URL}/api/openai/joycoachgpt?message=${encodeURIComponent(message)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${runtimeConfig.private.BACKEND_API_KEY}`
        }
      });
      return apiResponse;
    } catch (error) {
        // console.log('error', error);
        // // More information on error:
        // console.log('error.statusCode', error.statusCode);
        // console.log('error.message', error.message);
        // console.log('error.response', error.response);
        // console.log('error.body', error.body);
        
      event.res.statusCode = error.statusCode || 500;
      return { message: error.message };
    }
  });
  