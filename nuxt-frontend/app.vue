<template>
  <main>
    <client-only>
      <Toast ref="toast" position="bottom-right" style="transform:scale(0.9);margin-bottom:-10px;margin-right:-10px;"></Toast>
    </client-only>


    <ImageHeader />
    
    <div style="margin: 40px;">
      <div class="title-container">
      <h2>Describe your situation</h2>
    </div>

    <div class="textarea-container">
      <Textarea v-model="msg" 
              autoResize 
              rows="10" 
              class="textarea-mid-width" 
              :class="{ 'p-invalid': hasAttemptedSubmit && !isValidInput }" 
              placeholder="Describe the situation for which you desire coach's advice." />
  </div>

  <div class="button-container">
    <Button :label="buttonLabel" @click="handleButtonClick" :disabled="buttonDisabled" style="margin-top:3px;"/>
  </div>

  <div class="error-container">
    <small v-show="hasAttemptedSubmit && !isValidInput" class="p-error">Please enter at least 10 characters.</small>
  </div>

  <div class="response-container">
    <FormattedResponse v-if="serverResponseData" :response-data="serverResponseData" />
  </div>

</div>
    <Credits/>
  </main>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import Textarea from 'primevue/textarea';
import ImageHeader from './components/ImageHeader.vue';
import Button from 'primevue/button';
import FormattedResponse from './components/FormattedResponse.vue';
import Credits from './components/Credits.vue';

// Toast
import { useToast } from 'primevue/usetoast';

const toast = useToast();





const show429 = () => {
  if (process.client) {

  toast.add({
    severity: 'error',
    summary: 'Too many requests',
    detail: 'There have been too many requests to the coach. Please try again later.',
    life: 5000
  });

}
};

const showError = () => {
  if (process.client) {

  toast.add({
    severity: 'error',
    summary: 'An error occurred',
    detail: 'An error has occured, please try again.',
    life: 3000
  });

}
};


// Message and button

const msg = ref('');
const hasAttemptedSubmit = ref(false);
const isValidInput = computed(() => msg.value.length >= 10);
const buttonLabel = ref('Get Coached!');
const buttonDisabled = ref(false);
const serverResponse = ref('');
const serverResponseData = ref(null);
const allMessages = ['Reviewing your situation...', 'Consulting the book...', 'Shifting gears...', 'Formulating response...'];



async function handleButtonClick() {
  serverResponseData.value = null;
  hasAttemptedSubmit.value = true;
  if (isValidInput.value) {
    buttonDisabled.value = true;
    startMessageCycling();
    await fetchJoyCoachData();
    stopMessageCycling();
  }
}

let messageCyclingIntervalId = null;
function startMessageCycling() {
  let index = 0;
  messageCyclingIntervalId = setInterval(() => {
    if (index < allMessages.length) {
      buttonLabel.value = allMessages[index];
      index++;
    } else {
      index = 0;
    }
  }, 3000); // Cycle messages every 3 seconds
  buttonLabel.value = "Processing...";
}

function stopMessageCycling() {
  clearInterval(messageCyclingIntervalId);
  buttonLabel.value = 'Get Coached!'; // Reset button label
  buttonDisabled.value = false;
}




async function fetchJoyCoachData() {
  try {
    const queryParams = new URLSearchParams({ message: msg.value });

    console.log('Fetching data...')
    console.log(JSON.stringify({ message: msg.value }))

    const response = await fetch('https://coach.up.railway.app/api/joycoach', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: msg.value })
    });

    if (!response.ok) {
      if (response.status==429){
        show429();
      }
      else {
        showError();
      }
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    serverResponse.value = data;
    serverResponseData.value = data;

  } catch (error) {
    console.error('Fetch error:', error);
    serverResponse.value = 'Error: ' + error.message;
    serverResponseData.value = null; // Reset on error
  }
}

</script>


<style scoped>
.textarea-mid-width {
  width: 60%;
}

@media (max-width: 1000px) {
  .textarea-mid-width, .button-container {
    width: 80%; /* Adjust width for medium screens */
  }
}

@media (max-width: 600px) {
  .textarea-mid-width, .button-container {
    width: 95%; /* Adjust width for smaller screens */
  }
}

</style>
