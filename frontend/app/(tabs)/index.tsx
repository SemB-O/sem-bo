// app/index.tsx
import { View } from 'react-native';
import BrandTitle from '@/components/BrandTitle';
import PlanCard from '@/components/PlanCard';

export default function Home() {
  return (
    <View className="flex-1 items-center justify-center bg-white px-4 py-8 space-y-8">
      <BrandTitle text="Escolha" highlight="seu Plano" />

      <View className="flex-row flex-wrap justify-center gap-4">
        <PlanCard
          title="Viva"
          description="Para futuristas virados na parte da saúde"
          price="123,00"
          onPress={() => console.log('Selecionou Viva')}
        />
        <PlanCard
          title="La"
          description="Para médicos residentes"
          price="123,00"
          onPress={() => console.log('Selecionou La')}
        />
      </View>
    </View>
  );
}
