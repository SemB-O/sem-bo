import { useState } from 'react';
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  Pressable,
  Platform,
  StatusBar,
  useWindowDimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import BrandTitle from '@/components/BrandTitle';

export default function EnterNameScreen() {
  const [name, setName] = useState('');
  const router = useRouter();
  const { width } = useWindowDimensions();
  const isDesktop = width >= 768;

  const handleNext = () => {
    if (name.trim()) {
      console.log('Nome:', name);
      router.push('/choosePlan');
    }
  };

  return (
    <SafeAreaView
      className="flex-1 bg-white"
      style={{
        paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
      }}
    >
      <View className="flex-1 items-center justify-center px-6">
        <View
          style={{
            maxWidth: 400,
            width: '100%',
          }}
          className="w-full space-y-6"
        >
          <BrandTitle beforeText="Qual é seu " highlight="nome" afterText="?" isBbreakLineOnMobile="False" sizeClass = 'text-4xl'/>

          <TextInput
            value={name}
            onChangeText={setName}
            placeholder="Nome completo"
            placeholderTextColor="#888"
            className="w-full border border-gray-300 rounded-lg px-4 py-3 text-base text-black mt-2"
            align="left"
          />

          <Pressable
            onPress={handleNext}
            className="w-full bg-black py-3 rounded-lg mt-4"
          >
            <Text className="text-white text-center font-medium text-base">
              Avançar
            </Text>
          </Pressable>
        </View>
      </View>
    </SafeAreaView>
  );
}
