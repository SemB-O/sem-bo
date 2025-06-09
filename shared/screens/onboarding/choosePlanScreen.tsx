import { Text, View } from 'react-native';

type BrandTitleProps = {
  black: string;
  highlight: string;
};

function BrandTitle({ black, highlight }: BrandTitleProps) {
  return (
    <View className="flex-row items-end">
      <Text className="text-5xl font-bold text-black">{black}</Text>
      <Text className="text-5xl font-bold text-cyan-400">{highlight}</Text>
    </View>
  );
}


<BrandTitle black="Escolha" highlight="seu Plano" />
