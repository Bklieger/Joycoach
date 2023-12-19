<template>
    <div>
        <div class="ai-response">
            <i class="pi pi-user ai-icon"></i>
            <p class="message-text">{{ messageText }}</p>
        </div>

        <Divider />
        <div v-for="(skill, index) in skillSpecificResponses" :key="index">
            <Fieldset :legend="skill['skill-brief-title']" :toggleable="true" style="margin-top:20px;">
                <p class="skill-application">{{ skill['skill-application'] }}</p>
            </Fieldset>
        </div>
    </div>
</template>
  
  
<script>
import Fieldset from 'primevue/fieldset';
import Divider from 'primevue/divider';

export default {
    components: {
        Fieldset,
        Divider
    },
    props: {
        responseData: {
            type: Object,
            required: true
        }
    },
    computed: {
        parsedMessage() {
            try {
                return JSON.parse(this.responseData.message);
            } catch (e) {
                console.error('Error parsing JSON in message:', e);
                return {};
            }
        },
        messageText() {
            return this.parsedMessage.response_to_user || 'No message available';
        },
        skillSpecificResponses() {
            const skills = this.parsedMessage['skill-specific-responses'] || [];
            return skills;
        }
    }
}
</script>
  

<style scoped>
.message-text {
    font-size: 1.1em;
    color: #333;
    line-height: 1.6;
}

.skill-application {
    font-size: 1em;
    color: #555;
    line-height: 1.4;
}

.ai-response {
    display: flex;
    align-items: center;
    margin-top: 20px;
}

.ai-icon {
    font-size: 2em;
    border-radius: 50%;
    background-color: #f0f0f0;
    padding: 0.5em;
    margin-right: 10px;
}
</style>