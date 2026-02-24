import { SafeAreaView, View, Platform, StatusBar } from 'react-native';
import BrandTitle from '@/components/BrandTitle';
import PlanCard from '@/components/PlanCard';

export default function ChoosePlanScreen() {
  return (
    <SafeAreaView
      className="flex-1 bg-white"
      style={{
        paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
      }}
    >
      <View className="flex-1 items-center justify-center px-4 py-8 space-y-8">
        <BrandTitle beforeText="Escolha" highlight=" seu Plano" />

        <View className="flex-row flex-wrap justify-center gap-4">
          <PlanCard
            title="Viva"
            description="Texto de exemplo para o plano Viva."
            price="123,00"
            onPress={() => console.log('Selecionou Viva')}
          />
          <PlanCard
            title="La"
            description="Texto de exemplo para o plano La."
            price="123,00"
            onPress={() => console.log('Selecionou La')}
          />
        </View>
      </View>
    </SafeAreaView>
  );
}
